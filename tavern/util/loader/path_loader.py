import logging
import os.path
import json
import io
from jsonref import JsonLoader
import yaml
from .yaml_loader import IncludeLoader

logger = logging.getLogger(__name__)


class SchemaLoader(JsonLoader):
    def __init__(self):
        JsonLoader.__init__(self)
        self._base_dir = ""

    @property
    def base_dir(self):
        return self._base_dir

    @base_dir.setter
    def base_dir(self, base_dir):
        self._base_dir = base_dir

    def __call__(self, uri, **kwargs):
        if uri.startswith("/"):
            if not os.path.exists(uri):
                uri = os.path.join(self.base_dir, uri[1:])
        uri = os.path.normpath(uri)

        if uri in self.store and self.store[uri] == "parsing":
            logger.warning("Found rescursion:%s", uri)
            return {}
        elif uri in self.store:
            return self.store[uri]
        else:
            self.store[uri] = "parsing"
            result = self.get_remote_json(uri, **kwargs)
            if self.cache_results:
                self.store[uri] = result
            return result

    def load_json_file(self, stream, **kwargs):
        return json.load(stream, **kwargs)

    def load_yaml_file(self, stream, **kwargs):
        return yaml.load(stream, **kwargs)

    def get_remote_json(self, uri, **kwargs):
        filename = os.path.basename(uri)
        extension = os.path.splitext(filename)[1].lstrip('.')
        with io.open(uri, mode="r", encoding="utf-8") as stream:
            if extension in ('yaml', 'yml'):
                result = self.load_yaml_file(stream, **kwargs)
            elif extension == 'json':
                result = self.load_json_file(stream, **kwargs)

        return result


class YamlLoader(SchemaLoader):
    def load_yaml_file(self, stream, **kwargs):
        return yaml.load(stream, Loader=IncludeLoader)


schema_loader = SchemaLoader()
yaml_loader = YamlLoader()
