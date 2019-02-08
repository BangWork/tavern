import re
import logging
import random
from tavern.util.compat import basestring, builtin_str, integer_types

logger = logging.getLogger(__name__)


def random_string(num=8, checked=""):
    seed = "0123456789AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz"
    salt = []
    for _ in range(num):
        salt.append(random.choice(seed))
    random_string = checked + ''.join(salt)
    return random_string


def uuid(checked=""):
    return random_string(checked=checked)


# comparator
def equals(check_value, expect_value):
    if isinstance(check_value, dict):
        assert isinstance(expect_value, dict), "type not equal: '{}' != '{}'".format(
            check_value, expect_value)

        for key in check_value:
            assert key in expect_value, "key not equal:'{}' != '{}'".format(
                check_value, expect_value)
            equals(check_value[key], expect_value[key])
    elif isinstance(check_value, (list, tuple)):
        assert isinstance(expect_value, (list, tuple)), "type not equal: '{}' != '{}'".format(
            check_value, expect_value)
        assert len(check_value) == len(expect_value), "list length not equal:'{}' != '{}'".format(
            check_value, expect_value)

        for index, _ in enumerate(check_value):
            equals(check_value[index], expect_value[index])
    else:
        assert check_value == expect_value, "value '{}' != '{}'".format(
            check_value, expect_value)


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
