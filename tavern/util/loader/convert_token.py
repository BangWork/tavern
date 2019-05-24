from distutils.util import strtobool
from builtins import str as ustr
import yaml
from tavern.util.exceptions import InvalidTypeToConvertError
from .load_case import IncludeLoader


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
