import logging
from functools import wraps

from future.utils import raise_from

from . import exceptions

logger = logging.getLogger(__name__)


def run_with_times(stage):
    """Look for repeat and try to repeat the stage `times` times.

    Args:
        stage (dict): test stage
    """

    times = stage.get('times', 1)

    if times == 1:
        # Just return the plain function
        return lambda fn: fn

    def retry_wrapper(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            logger.info("Stage times: '%i'", times)
            for i in range(times):
                try:
                    res = fn(*args, **kwargs)
                    logger.info("Stage '%s' repeat for %i time.", stage['name'], i + 1)
                except exceptions.TavernException as e:
                    raise_from(
                        exceptions.TestFailError(
                            "Test '{}' failed: stage did not succeed,running by times stopped,current times:{}".format(stage['name'], i)),
                        e)
                    break

            return res

        return wrapped

    return retry_wrapper
