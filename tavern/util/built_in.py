import re
import logging
import random
from .compat import basestring, builtin_str, integer_types
from .dict_util import check_keys_match_recursive

logger = logging.getLogger(__name__)


def random_string(length=8, checked="", has_number=True, has_upcase=True, has_lowercase=True):
    seed = []
    if has_number:
        seed.append("0123456789")
    if has_upcase:
        seed.append("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if has_lowercase:
        seed.append("abcdefghijklmnopqrstuvwxyz")

    seed_str = "".join(seed)
    salt = []
    for _ in range(length):
        salt.append(random.choice(seed_str))
    return checked + ''.join(salt)


def uuid(checked=""):
    return random_string(checked=checked)


# comparator
def equals(check_value, expect_value, **kwargs):
    check_keys_match_recursive(expect_value, check_value, [], **kwargs)


def less_than(check_value, expect_value):
    assert check_value < expect_value


def less_than_or_equals(check_value, expect_value):
    assert check_value <= expect_value


def greater_than(check_value, expect_value):
    assert check_value > expect_value


def greater_than_or_equals(check_value, expect_value):
    assert check_value >= expect_value


def not_equals(check_value, expect_value):
    assert check_value != expect_value


def string_equals(check_value, expect_value):
    assert builtin_str(check_value) == builtin_str(expect_value)


def length_equals(check_value, expect_value):
    assert isinstance(expect_value, integer_types)
    assert len(check_value) == expect_value


def length_greater_than(check_value, expect_value):
    assert isinstance(expect_value, integer_types)
    assert len(check_value) > expect_value


def length_greater_than_or_equals(check_value, expect_value):
    assert isinstance(expect_value, integer_types)
    assert len(check_value) >= expect_value


def length_less_than(check_value, expect_value):
    assert isinstance(expect_value, integer_types)
    assert len(check_value) < expect_value


def length_less_than_or_equals(check_value, expect_value):
    assert isinstance(expect_value, integer_types)
    assert len(check_value) <= expect_value


def contains(check_value, expect_value):
    assert isinstance(check_value, (list, tuple, dict, basestring))
    assert expect_value in check_value


def contained_by(check_value, expect_value):
    assert isinstance(expect_value, (list, tuple, dict, basestring))
    assert check_value in expect_value


def type_match(check_value, expect_value):
    def get_type(name):
        if isinstance(name, type):
            return name
        elif isinstance(name, basestring):
            try:
                return __builtins__[name]
            except KeyError:
                raise ValueError(name)
        else:
            raise ValueError(name)

    assert isinstance(check_value, get_type(expect_value))


def regex_match(check_value, expect_value):
    assert isinstance(expect_value, basestring)
    assert isinstance(check_value, basestring)
    assert re.match(expect_value, check_value)


def startswith(check_value, expect_value):
    assert builtin_str(check_value).startswith(builtin_str(expect_value))


def endswith(check_value, expect_value):
    assert builtin_str(check_value).endswith(builtin_str(expect_value))
