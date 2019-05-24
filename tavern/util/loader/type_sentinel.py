import logging
import pytest
from future.utils import raise_from
import yaml

from tavern.util.exceptions import BadSchemaError
from .load_case import IncludeLoader


logger = logging.getLogger(__name__)


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
