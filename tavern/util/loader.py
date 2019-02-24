# https://gist.github.com/joshbode/569627ced3076931b02f

from distutils.util import strtobool
import logging
import uuid
import os.path
import pytest
import json
from builtins import str as ustr
from jsonref import JsonLoader, load_uri, JsonRef
from future.utils import raise_from

try:
    # If requests >=1.0 is available, we will use it
    import requests

    if not callable(requests.Response.json):
        requests = None
except ImportError:
    requests = None


try:
    from urllib import parse as urlparse
    from urllib.request import pathname2url, urlopen
except ImportError:
    import urlparse  # type: ignore
    from urllib2 import urlopen
    from urllib import pathname2url  # type: ignore


import yaml
from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.parser import Parser
from yaml.composer import Composer
from yaml.constructor import SafeConstructor
from yaml.resolver import Resolver

from tavern.util.exceptions import BadSchemaError, InvalidTypeToConvertError


logger = logging.getLogger(__name__)


def makeuuid(loader, node):
    # pylint: disable=unused-argument
    return str(uuid.uuid4())


class RememberComposer(Composer):

    """A composer that doesn't forget anchors across documents
    """

    def compose_document(self):
        # Drop the DOCUMENT-START event.
        self.get_event()

        # Compose the root node.
        node = self.compose_node(None, None)

        # Drop the DOCUMENT-END event.
        self.get_event()

        # If we don't drop the anchors here, then we can keep anchors across
        # documents.
        # self.anchors = {}

        return node


def create_node_class(cls):
    class node_class(cls):
        def __init__(self, x, start_mark, end_mark):
            cls.__init__(self, x)
            self.start_mark = start_mark
            self.end_mark = end_mark

        # def __new__(self, x, start_mark, end_mark):
        #     return cls.__new__(self, x)
    node_class.__name__ = '%s_node' % cls.__name__
    return node_class


dict_node = create_node_class(dict)
list_node = create_node_class(list)


class SourceMappingConstructor(SafeConstructor):
    # To support lazy loading, the original constructors first yield
    # an empty object, then fill them in when iterated. Due to
    # laziness we omit this behaviour (and will only do "deep
    # construction") by first exhausting iterators, then yielding
    # copies.
    def construct_yaml_map(self, node):
        obj, = SafeConstructor.construct_yaml_map(self, node)
        return dict_node(obj, node.start_mark, node.end_mark)

    def construct_yaml_seq(self, node):
        obj, = SafeConstructor.construct_yaml_seq(self, node)
        return list_node(obj, node.start_mark, node.end_mark)


SourceMappingConstructor.add_constructor(
    u'tag:yaml.org,2002:map',
    SourceMappingConstructor.construct_yaml_map)

SourceMappingConstructor.add_constructor(
    u'tag:yaml.org,2002:seq',
    SourceMappingConstructor.construct_yaml_seq)

yaml.add_representer(
    dict_node, yaml.representer.SafeRepresenter.represent_dict)
yaml.add_representer(
    list_node, yaml.representer.SafeRepresenter.represent_list)


# pylint: disable=too-many-ancestors
class IncludeLoader(Reader, Scanner, Parser, RememberComposer, Resolver,
                    SourceMappingConstructor, SafeConstructor):
    """YAML Loader with `!include` constructor and which can remember anchors
    between documents"""

    def __init__(self, stream, base_dir=None):
        """Initialise Loader."""

        # pylint: disable=non-parent-init-called
        self._base_dir = base_dir
        try:
            self._root = os.path.split(stream.name)[0]
        except AttributeError:
            self._root = os.path.curdir
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        RememberComposer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)
        SourceMappingConstructor.__init__(self)


def get_filepath(base_dir, parent, filename):
    if filename.startswith("/"):
        if not os.path.exists(filename) and base_dir is not None:
            abs_path = os.path.join(base_dir, filename[1:])
            logger.debug("absolute path base on loader._base_dir:%s", abs_path)
            if os.path.exists(abs_path):
                filename = abs_path
            else:
                raise BadSchemaError(
                    "Unreachable absolute path base on base_dir,'{}'".format(
                        abs_path)
                )
        else:
            raise BadSchemaError(
                "Unreachable absolute path '{}'".format(filename))
    else:
        filename = os.path.abspath(os.path.join(parent, filename))

    return filename


def is_uri(uri):
    parse_result = urlparse.urlparse(uri)
    if parse_result.scheme != "":
        return True
    return False


class JSONSchemaLoader(JsonLoader):
    def __init__(self, base_path, parent_path):
        JsonLoader.__init__(self)
        self.base_path = base_path
        self.parent_path = parent_path

    def __call__(self, uri, **kwargs):
        if not is_uri(uri):
            path = get_filepath(self.base_path, self.parent_path, uri)
            uri = urlparse.urljoin('file:', pathname2url(path))
        return JsonLoader.__call__(self, uri, **kwargs)

    def get_remote_json(self, uri, **kwargs):
        scheme = urlparse.urlsplit(uri).scheme
        if scheme in ["http", "https"] and requests:
            # Prefer requests, it has better encoding detection
            response = requests.get(uri)
            try:
                response.json(**kwargs)
            except TypeError:
                logger.warn(
                    "requests >=1.2 required for custom kwargs to json.loads")
                result = response.json()
            except ValueError:
                # try to parsed content with yaml if parse failed
                result = yaml.load(response.content)
        else:
            # Otherwise, pass off to urllib and assume utf-8
            filename = os.path.basename(uri)
            extension = os.path.splitext(filename)[1].lstrip('.')
            content = urlopen(uri).read().decode("utf-8")
            if extension in ('yaml', 'yml'):
                result = yaml.load(content)
            elif extension == 'json':
                result = json.loads(content, **kwargs)

        return result


def construct_resolve_reflink(loader, node):
    """Include file referenced at node."""
    # pylint: disable=protected-access
    filename = loader.construct_scalar(node)

    loader = JSONSchemaLoader(loader._base_dir, loader._root)
    return load_uri(filename, loader=loader)


def construct_resolve_ref(loader, node):
    # pylint: disable=protected-access
    value = loader.construct_mapping(node)

    loader = JSONSchemaLoader(loader._base_dir, loader._root)

    return JsonRef.replace_refs(value, loader=loader)


def construct_include(loader, node):
    """Include file referenced at node."""
    # pylint: disable=protected-access
    filename = loader.construct_scalar(node)

    extension = os.path.splitext(filename)[1].lstrip('.')
    if extension not in ('yaml', 'yml'):
        raise BadSchemaError("Unknown filetype '{}'".format(filename))

    filename = get_filepath(loader._base_dir, loader._root, filename)

    def get_loader(stream):
        return IncludeLoader(stream, loader._base_dir)

    with open(filename, 'r') as f:
        return yaml.load(f, get_loader)


IncludeLoader.add_constructor("!include", construct_include)
IncludeLoader.add_constructor("!uuid", makeuuid)
IncludeLoader.add_constructor("!resolve_reflink", construct_resolve_reflink)
IncludeLoader.add_constructor("!resolve_ref", construct_resolve_ref)


class TypeSentinel(yaml.YAMLObject):
    """This is a sentinel for expecting a type in a response. Any value
    associated with these is going to be ignored - these are only used as a
    'hint' to the validator that it should expect a specific type in the
    response.
    """
    yaml_loader = IncludeLoader

    @classmethod
    def from_yaml(cls, loader, node):
        return cls()

    def __str__(self):
        return "<Tavern YAML sentinel for {}>".format(self.constructor)  # pylint: disable=no-member

    @classmethod
    def to_yaml(cls, dumper, data):
        node = yaml.nodes.ScalarNode(
            cls.yaml_tag, "", style=cls.yaml_flow_style)
        return node


class IntSentinel(TypeSentinel):
    yaml_tag = "!anyint"
    constructor = int


class FloatSentinel(TypeSentinel):
    yaml_tag = "!anyfloat"
    constructor = float


class StrSentinel(TypeSentinel):
    yaml_tag = "!anystr"
    constructor = str


class BoolSentinel(TypeSentinel):
    yaml_tag = "!anybool"
    constructor = bool


class AnythingSentinel(TypeSentinel):
    yaml_tag = "!anything"
    constructor = "anything"

    @classmethod
    def from_yaml(cls, loader, node):
        return ANYTHING

    def __deepcopy__(self, memo):
        """Return ANYTHING when doing a deep copy

        This is required because the checks in various parts of the code assume
        that ANYTHING is a singleton, but doing a deep copy creates a new object
        by default
        """
        return ANYTHING


# One instance of this (see above)
ANYTHING = AnythingSentinel()


class TypeConvertToken(yaml.YAMLObject):
    """This is a sentinel for something that should be converted to a different
    type. The rough load order is:

    1. Test data is loaded for schema validation
    2. Test data is dumped again so that pykwalify can read it (the actual
        values don't matter at all at this point, because we're just checking
        that the structure is correct)
    3. Test data is loaded and formatted

    So this preserves the actual value that the type should be up until the
    point that it actually needs to be formatted
    """
    yaml_loader = IncludeLoader

    def __init__(self, value):
        self.value = value

    @classmethod
    def from_yaml(cls, loader, node):
        value = loader.construct_scalar(node)

        if not isinstance(value, (ustr, str)):
            raise InvalidTypeToConvertError(
                "Type convert only valid for str value")

        try:
            # See if it's already a valid value (eg, if we do `!int "2"`)
            converted = cls.constructor(value)  # pylint: disable=no-member
        except ValueError:
            # If not (eg, `!int "{int_value:d}"`)
            return cls(value)
        else:
            return converted

    @classmethod
    def to_yaml(cls, dumper, data):
        return yaml.nodes.ScalarNode(cls.yaml_tag, data.value, style=cls.yaml_flow_style)


class IntToken(TypeConvertToken):
    yaml_tag = "!int"
    constructor = int


class FloatToken(TypeConvertToken):
    yaml_tag = "!float"
    constructor = float


class StrToBoolConstructor(object):
    """Using `bool` as a constructor directly will evaluate all strings to `True`."""

    def __new__(cls, s):
        return bool(strtobool(s))


class BoolToken(TypeConvertToken):
    yaml_tag = "!bool"
    constructor = StrToBoolConstructor


class StrToRawConstructor(object):
    """Used when we want to ignore brace formatting syntax"""

    def __new__(cls, s):
        return str(s.replace("{", "{{").replace("}", "}}"))


class RawStrToken(TypeConvertToken):
    yaml_tag = "!raw"
    constructor = StrToRawConstructor


# Sort-of hack to try and avoid future API changes
ApproxScalar = type(pytest.approx(1.0))


class ApproxSentinel(yaml.YAMLObject, ApproxScalar):
    yaml_tag = "!approx"
    yaml_loader = IncludeLoader

    @classmethod
    def from_yaml(cls, loader, node):
        # pylint: disable=unused-argument
        try:
            val = float(node.value)
        except (ValueError, TypeError) as e:
            logger.error(
                "Could not coerce '%s' to a float for use with !approx", type(node.value))
            raise_from(BadSchemaError, e)

        return pytest.approx(val)

    @classmethod
    def to_yaml(cls, dumper, data):
        return yaml.nodes.ScalarNode("!approx", str(data.expected), style=cls.yaml_flow_style)


# Apparently this isn't done automatically?
yaml.dumper.Dumper.add_representer(ApproxScalar, ApproxSentinel.to_yaml)
