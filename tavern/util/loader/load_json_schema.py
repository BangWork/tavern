import logging
import os.path
from jsonref import load_uri, JsonRef

try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse  # type: ignore

from .path_loader import schema_loader
from .yaml_loader import IncludeLoader

logger = logging.getLogger(__name__)


def construct_resolve_reflink(loader, node):
    """Include file referenced at node."""
    # pylint: disable=protected-access
    filename = loader.construct_scalar(node)
    file_path = os.path.join(loader._root, filename)
    return load_uri(file_path, loader=schema_loader)


def construct_resolve_ref(loader, node):
    # pylint: disable=protected-access
    value = loader.construct_mapping(node)
    base_uri = os.path.join(loader._root, "root.json")
    return JsonRef.replace_refs(value, loader=schema_loader, base_uri=base_uri)


IncludeLoader.add_constructor("!resolve_reflink", construct_resolve_reflink)
IncludeLoader.add_constructor("!resolve_ref", construct_resolve_ref)
