from jsonschema import validate
from jsonref import load_uri, JsonRef
from .compat import basestring


class JsonschemaValidator(object):
    def __init__(self):
        self._loader = None

    def configure(self, **kwargs):
        if "loader" in kwargs:
            self._loader = kwargs["loader"]

    def validate(self, check_value, schema):
        if isinstance(schema, basestring):
            schema = load_uri(schema, loader=self._loader)
        else:
            schema = JsonRef.replace_refs(schema, loader=self._loader)
        validate(check_value, schema)


jsonschema_validator = JsonschemaValidator()
