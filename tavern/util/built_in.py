import re
import logging
import random
from future.utils import raise_from
from . import exceptions
from .compat import basestring, builtin_str, integer_types
from .dict_util import check_keys_match_recursive
from functools import reduce
from jsonschema import validate

logger = logging.getLogger(__name__)


def random_string(length=8, prefix="", has_number=True, has_uppercase=True, has_lowercase=True):
    seed = []
    if has_number:
        seed.append("0123456789")
    if has_uppercase:
        seed.append("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if has_lowercase:
        seed.append("abcdefghijklmnopqrstuvwxyz")

    seed_str = "".join(seed)
    salt = []
    for _ in range(length):
        salt.append(random.choice(seed_str))
    return prefix + ''.join(salt)


def uuid(prefix=""):
    return random_string(prefix=prefix)

# comparator


def jsonschema_validation(check_value, schema):
    validate(check_value, schema)


def unique_item_properties(check_value, keys_or_indexs):
    assert isinstance(
        check_value, (list, tuple)), "Check value for unique_item_properties must be list or tuple, value is: %s" % check_value
    if not isinstance(keys_or_indexs, (list, tuple)):
        keys_or_indexs = [keys_or_indexs]
    exist = {}
    for index, item in enumerate(check_value):
        assert isinstance(item, (dict, list, tuple)
                          ), "item in Check value for unique_item_properties must be collection,value is: {},index is: {}".format(item, index)

        for key_or_index in keys_or_indexs:
            if key_or_index not in exist:
                exist[key_or_index] = []

            value = item[key_or_index]
            assert value not in exist[key_or_index], "Found duplicate value, index is {} - {}".format(
                exist[key_or_index].index(value), index)

            exist[key_or_index].append(value)


def equals(check_value, expect_value, **kwargs):
    check_keys_match_recursive(expect_value, check_value, [], **kwargs)


def element_equals_with_index(check_list, expect_value, **kwargs):
    assert isinstance(check_list, (list, tuple)
                      ), "Check list for element_equals_with_index must be list or tuple, given value is %s" % check_list

    index = kwargs["index"]
    if abs(index) >= len(check_list):
        raise_from(exceptions.MissingFormatError(
            """
            List index out of range, list is {}, index is {}
            """.format(check_list, index)))
    else:
        equals(check_list[index], expect_value)


def equals_ignore_order(check_list, expect_list, **kwargs):
    assert isinstance(check_list, (list, tuple)
                      ), "Check list for equal_ignore_order must be list or tuple, given value is %s" % check_list
    assert isinstance(expect_list, (list, tuple)
                      ), "Expect list for equal_ignore_order must be list or tuple, given value is %s" % check_list
    assert len(check_list) == len(expect_list)
    check_key = None
    if "check_key" in kwargs:
        check_key = kwargs["check_key"]
    if not check_key:
        # list, tuple
        if isinstance(check_list[0], (list, tuple)):
            for i in range(len(check_list)):
                equals_ignore_order(check_list[i], expect_list[i])
        # string, number, boolean
        elif set(check_list) != set(expect_list):
            raise AssertionError(
                """
                When ignore order, two lists are not equal. Check list is {}, expect list is {}
                """.format(check_list, check_list))
    # dict, check_key must be string or number
    else:
        ckeys = []
        for i in check_list:
            ckeys.append(i[check_key])

        ekeys = []
        for i in expect_list:
            ekeys.append(i[check_key])
        equals_ignore_order(ckeys, ekeys)


def list_equals_by_sorted_key(check_list, expect_list, **kwargs):
    assert isinstance(check_list, (list, tuple)
                      ), "Check list for list_equals_by_sorted_key must be list or tuple, given value is %s" % check_list
    assert isinstance(expect_list, (list, tuple)
                      ), "Expect list for list_equals_by_sorted_key must be list or tuple, given value is %s" % check_list
    assert len(check_list) == len(expect_list)

    sort_key = kwargs["sort_key"]
    check_list = sorted(check_list, key=lambda e: e.__getitem__(sort_key))
    if "check_key" in kwargs:
        check_key = kwargs["check_key"]

        def save_check_key(item):
            return item[check_key]
        check_list = map(save_check_key, check_list)

    equals(check_list, expect_list)


def unique_item_in_list(check_list):
    checked = []
    for i in check_list:
        if i in checked:
            raise AssertionError(
                """
                element is not unique in list, element is {}, check_list is {}
                """.format(i, check_list))
        else:
            checked.append(i)
    return True


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


def not_contains(check_value, expect_value):
    assert isinstance(check_value, (list, tuple, dict, basestring))
    assert expect_value not in check_value


def contains(check_value, expect_value):
    assert isinstance(check_value, (list, tuple, dict, basestring))
    assert expect_value in check_value


def _list_contains(check_list, check_value, **kwargs):
    assert isinstance(check_list, (list, tuple)
                      ), "Check list must be list or tuple, given value is %s" % check_list
    check_key = kwargs["check_key"] if "check_key" in kwargs else None
    unique_key = kwargs["unique_key"] if "unique_key" in kwargs else None

    # unique_key in check_value
    if unique_key:
        for i in check_list:
            if check_value[unique_key] == i[unique_key]:
                return True
        return False
    elif check_key:
        if isinstance(check_key, (list, tuple)):
            for i in check_list:
                element = {}
                for key in check_key:
                    element[key] = i[key]
                if check_value == element:
                    return True
            return False
        else:
            for i in check_list:
                if check_value == i[check_key]:
                    return True
            return False


def list_contains_with_items(check_list, check_value, **kwargs):
    if not _list_contains(check_list, check_value, **kwargs):
        raise AssertionError("%s not found in %s" % (check_value, check_list))
    return


def list_not_contains_with_items(check_list, check_value, **kwargs):
    if _list_contains(check_list, check_value, **kwargs):
        raise AssertionError("%s not found in %s" % (check_value, check_list))
    return


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
