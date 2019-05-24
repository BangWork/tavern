import uuid
from .yaml_loader import IncludeLoader


def makeuuid(loader, node):
    # pylint: disable=unused-argument
    return str(uuid.uuid4())


IncludeLoader.add_constructor("!uuid", makeuuid)
