import logging
import re
import importlib
from future.utils import raise_from
from tavern.util.exceptions import InvalidExtFunctionError

logger = logging.getLogger(__name__)


def import_ext_function(entrypoint):
    """Given a function name in the form of a setuptools entry point, try to
    dynamically load and return it

    Args:
        entrypoint (str): setuptools-style entrypoint in the form
            module.submodule:function

    Returns:
        function: function loaded from entrypoint

    Raises:
        InvalidExtFunctionError: If the module or function did not exist
    """
    match = re.match(r"^(([\w_\.]+):)?([\w_]+)$", entrypoint)

    if not match:
        msg = "Expected entrypoint in the form module.submodule:function or builtin_function"
        logger.exception(msg)
        raise InvalidExtFunctionError(msg)

    module = match.group(2)
    funcname = match.group(3)

    if not module:
        module = "tavern.util.built_in"

    try:
        module = importlib.import_module(module)
    except ImportError as e:
        msg = "Error importing module {}".format(module)
        logger.exception(msg)
        raise_from(InvalidExtFunctionError(msg), e)

    try:
        function = getattr(module, funcname)
    except AttributeError as e:
        msg = "No function named {} in {}".format(funcname, module)
        logger.exception(msg)
        raise_from(InvalidExtFunctionError(msg), e)

    return function
