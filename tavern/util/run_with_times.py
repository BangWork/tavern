import logging
from functools import wraps

from future.utils import raise_from

from . import exceptions

logger = logging.getLogger(__name__)


def run_with_times(stage):
    """Look for retry and try to repeat the stage `retry` times.

    Args:
        stage (dict): test stage
    """

    times = stage.get('times', 0)

    if times == 0:
        # Just return the plain function
        return lambda fn: fn

    def retry_wrapper(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            for i in range(times + 1):
                try:
                    res = fn(*args, **kwargs)
                except exceptions.TavernException as e:
                    raise_from(
                        exceptions.TestFailError(
                            "Test '{}' failed: stage did not succeed,running by times stopped,current times:{}".format(stage['name'], i)),
                        e)
                else:
                    break

            return res

        return wrapped

    return retry_wrapper
