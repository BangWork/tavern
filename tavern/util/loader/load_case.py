import logging
import os.path
from .yaml_loader import IncludeLoader
from .path_loader import yaml_loader

logger = logging.getLogger(__name__)


def construct_include(loader, node):
    """Include file referenced at node."""
    # pylint: disable=protected-access
    file_path = loader.construct_scalar(node)
    file_path = os.path.join(loader._root, file_path)
    return yaml_loader(file_path)


IncludeLoader.add_constructor("!include", construct_include)
