import re
import logging
import json
from deepdiff import DeepDiff
from tavern.util.compat import basestring, builtin_str, integer_types

logger = logging.getLogger(__name__)


# def dict_equal(src_data, dst_data):
#     assert type(src_data) == type(dst_data), "type: '{}' != '{}'".format(
#         type(src_data), type(dst_data))
#     if isinstance(src_data, dict):
#         for key in src_data:
#             assert dst_data.has_key(key)
#             dict_equal(src_data[key], dst_data[key])
#     elif isinstance(src_data, list):
#         for src_list, dst_list in zip(sorted(src_data), sorted(dst_data)):
#             dict_equal(src_list, dst_list)
#     else:
#         assert src_data == dst_data, "value '{}' != '{}'".format(
#             src_data, dst_data)


# def list_equal(src_data, dst_data):
#     assert len(src_data) == len(dst_data)
#     if len(src_data) == len(dst_data):
#         for i in range(len(src_data)):
#             dict_equal(src_data[i], dst_data[i])


def deep_equal(check_value, expect_value):
    diff = DeepDiff(check_value, expect_value)
    diff_keys_length = len(diff.keys())
    assert diff_keys_length == 0, json.dumps(diff, indent=4)


def equal(check_value, expect_value):
    assert check_value == expect_value


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
