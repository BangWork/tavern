import re
import logging
import random
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
            value = item[key_or_index]
            if key_or_index not in exist:
                exist[key_or_index] = {value: index}
            else:
                assert value not in exist[key_or_index], "Found duplicate value, index is {} - {}".format(
                    exist[key_or_index][value], index)

def equals(check_value, expect_value, **kwargs):
    check_keys_match_recursive(expect_value, check_value, [], **kwargs)

def equal_ignore_order(check_list, expect_list):
    assert isinstance(check_list, list) and isinstance(expect_list, list)
    assert len(check_list) == len(check_list)
    
    return equals(check_list.sort(), expect_list.sort())

def sorted_by_key(check_list, check_key, **kwargs):
    list_in_dict = []
    sort_key = kwargs["sort_key"]
    expect_list = kwargs["expect_list"]
    check_list = sorted(check_list,key = lambda e:e.__getitem__(sort_key))
    for i in check_list:
        for key,value in i.items():
            if key == check_key:
                list_in_dict.append(value)
    return equals(list_in_dict, expect_list)

def unique_item_in_list(check_list, check_value):
    assert check_value in check_list
    no_duplicate_elements(check_list)

def element_index(check_list, check_value, **kwargs):
    for index, element in enumerate(check_list):
        if index == kwargs["expect_index"]:
            return equals(element, check_value)

def element_equals(check_list, check_value):
    assert isinstance(check_list, list)
    if check_list:
        for i in check_list:
            equals(i, check_value)

def remove_duplicate_elements(check_list):
    func = lambda x,y:x if y in x else x + [y]
    return reduce(func, [[], ] + check_list)

def no_duplicate_elements(check_list):
    expect_list = remove_duplicate_elements(check_list)
    equals(check_list, expect_list)

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



