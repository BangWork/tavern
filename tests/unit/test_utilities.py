from textwrap import dedent
import jsonschema
from mock import Mock, patch
from collections import OrderedDict

import pytest
import yaml
import copy
from builtins import str as ustr

from tavern.schemas.extensions import validate_extensions, validate_block
from tavern.util import exceptions
from tavern.util.loader import ANYTHING, IncludeLoader
from tavern.util.dict_util import deep_dict_merge, check_keys_match_recursive, format_keys
from tavern.util.built_in import unique_item_properties, jsonschema_validation


class TestValidateFunctions:

    def test_get_extension(self):
        """Loads a validation function correctly

        This doesn't check the signature at the time of writing
        """

        spec = {
            "$ext": {
                "function": "operator:add",
            }
        }

        validate_extensions(spec, None, None)

    def test_get_built_in_extension(self):
        """Loads tavern built in extention function
        """

        spec = {
            '$ext': {
                "function": "random_string",
                "extra_args": [4]
            }
        }

        validate_extensions(spec, None, None)

    def test_get_invalid_module(self):
        """Nonexistent module
        """

        spec = {
            "$ext": {
                "function": "bleuuerhug:add",
            }
        }

        with pytest.raises(exceptions.BadSchemaError):
            validate_extensions(spec, None, None)

    def test_get_nonexistent_function(self):
        """No name in module
        """

        spec = {
            "$ext": {
                "function": "os:aaueurhg",
            }
        }

        with pytest.raises(exceptions.BadSchemaError):
            validate_extensions(spec, None, None)


class TestValidateBlock:
    def test_validate_block(self):
        """valid validator
        """
        spec = [
            # equal
            {
                "eq": ["a", "a"]
            },
            {
                "equals": ["a", "a"]
            },
            {
                "==": ["a", "a"]
            },
            {
                "is": ["a", "a"]
            },

            # less_than
            {
                "lt": ["a", "a"]
            },
            {
                "less_than": ["a", "a"]
            },

            # less_than_or_equals
            {
                "le": ["a", "a"]
            },
            {
                "less_than_or_equals": ["a", "a"]
            },

            # greater_than
            {
                "gt": ["a", "a"]
            },
            {
                "greater_than": ["a", "a"]
            },

            # greater_than_or_equals
            {
                "ge": ["a", "a"]
            },
            {
                "greater_than_or_equals": ["a", "a"]
            },
            # not_equals
            {
                "ne": ["a", "a"]
            },
            {
                "not_equals": ["a", "a"]
            },
            # string_equals
            {
                "str_eq": ["a", "a"]
            },
            {
                "string_equals": ["a", "a"]
            },

            # length_equals
            {
                "len_eq": ["a", "a"]
            },
            {
                "length_equals": ["a", "a"]
            },
            {
                "count_eq": ["a", "a"]
            },

            # length_greater_than
            {
                "len_gt": ["a", "a"]
            },
            {
                "count_gt": ["a", "a"]
            },
            {
                "length_greater_than": ["a", "a"]
            },
            {
                "count_greater_than": ["a", "a"]
            },

            # length_greater_than_or_equals
            {
                "len_ge": ["a", "a"]
            },
            {
                "count_ge": ["a", "a"]
            },
            {
                "length_greater_than_or_equals": ["a", "a"]
            },
            {
                "count_greater_than_or_equals": ["a", "a"]
            },

            # length_less_than
            {
                "len_lt": ["a", "a"]
            },
            {
                "count_lt": ["a", "a"]
            },
            {
                "length_less_than": ["a", "a"]
            },
            {
                "count_less_than": ["a", "a"]
            },

            # length_less_than_or_equals
            {
                "len_le": ["a", "a"]
            },
            {
                "count_le": ["a", "a"]
            },
            {
                "length_less_than_or_equals": ["a", "a"]
            },
            {
                "count_less_than_or_equals": ["a", "a"]
            },
            {
                "$ext": {
                    "function": "random_string",
                    "extra_args": [1]
                }
            },
            {
                "$ext": {
                    "function": "random_string",
                    "extra_args": [1],
                    "extra_kwargs":{
                        "checked": "123"
                    }
                }
            }
        ]
        validate_block(spec, None, None)

    def test_not_valid_block(self):
        """Not valid comparators
        """
        spec = [
            {
                "not_valid": ["b", "b"]
            }
        ]

        with pytest.raises(exceptions.BadSchemaError):
            validate_block(spec, None, None)


class TestComparator:
    def test_jsonschema_validation_with_schema_object(self):
        """ test if check_value match jsonschema
        """
        check_value = {"a": 1}
        schema = {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "const": 1
                }
            }
        }
        jsonschema_validation(check_value, schema)

    def test_jsonschema_validation_with_schema_object_failed(self):
        check_value = {"a": 1}
        schema = {
            "type": "object",
            "properties": {
                "a": {
                    "type": "string"
                }
            }
        }
        with pytest.raises(jsonschema.exceptions.ValidationError):
            jsonschema_validation(check_value, schema)

    def test_unique_item_properties_failed(self):
        """ test if check_value has any item has duplicate value of key
        """
        check_value = [{"a": 1, "b": 3}, {"a": 1, "b": 2}]

        with pytest.raises(AssertionError):
            unique_item_properties(check_value, "a")

    def test_unique_item_properties_success(self):
        check_value = [{"a": 1, "b": 3}, {"a": 2, "b": 2}]
        unique_item_properties(check_value, "a")

    def test_unique_item_properties_bad_check_value(self):
        bad_value1 = {}
        bad_value2 = ["1"]
        with pytest.raises(AssertionError):
            unique_item_properties(bad_value1, "a")

        with pytest.raises(AssertionError):
            unique_item_properties(bad_value2, "a")


class TestDictMerge:

    def test_single_level(self):
        """ Merge two depth-one dicts with no conflicts
        """
        dict_1 = {
            'key_1': 'original_value_1',
            'key_2': 'original_value_2'
        }
        dict_2 = {
            'key_2': 'new_value_2',
            'key_3': 'new_value_3'
        }

        result = deep_dict_merge(dict_1, dict_2)

        assert dict_1 == {
            'key_1': 'original_value_1',
            'key_2': 'original_value_2'
        }
        assert dict_2 == {
            'key_2': 'new_value_2',
            'key_3': 'new_value_3'
        }
        assert result == {
            'key_1': 'original_value_1',
            'key_2': 'new_value_2',
            'key_3': 'new_value_3',
        }

    def test_recursive_merge(self):
        """ Merge two depth-one dicts with no conflicts
        """
        dict_1 = {
            'key': {
                'deep_key_1': 'original_value_1',
                'deep_key_2': 'original_value_2'
            }
        }
        dict_2 = {
            'key': {
                'deep_key_2': 'new_value_2',
                'deep_key_3': 'new_value_3'
            }
        }

        result = deep_dict_merge(dict_1, dict_2)

        assert dict_1 == {
            'key': {
                'deep_key_1': 'original_value_1',
                'deep_key_2': 'original_value_2'
            }
        }
        assert dict_2 == {
            'key': {
                'deep_key_2': 'new_value_2',
                'deep_key_3': 'new_value_3'
            }
        }
        assert result == {
            'key': {
                'deep_key_1': 'original_value_1',
                'deep_key_2': 'new_value_2',
                'deep_key_3': 'new_value_3'
            }
        }


class TestMatchRecursive:

    def test_match_dict(self):
        a = {
            "a": [
                {
                    "b": "val",
                },
            ]
        }
        b = copy.deepcopy(a)

        check_keys_match_recursive(a, b, [])

    def test_match_dict_mismatch(self):
        a = {
            "a": [
                {
                    "b": "val",
                },
            ]
        }
        b = copy.deepcopy(a)

        b["a"][0]["b"] = "wrong"

        with pytest.raises(exceptions.KeyMismatchError):
            check_keys_match_recursive(a, b, [])

    def test_match_nested_list(self):
        a = {
            "a": [
                "val"
            ]
        }
        b = copy.deepcopy(a)

        b["a"][0] = "wrong"

        with pytest.raises(exceptions.KeyMismatchError):
            check_keys_match_recursive(a, b, [])

    def test_match_nested_list_length(self):
        a = {
            "a": [
                "val"
            ]
        }
        b = copy.deepcopy(a)

        b["a"].append("wrong")

        with pytest.raises(exceptions.KeyMismatchError):
            check_keys_match_recursive(a, b, [])

    # These ones are testing 'internal' behaviour, might break in future

    def test_match_nested_anything_dict(self):
        a = {
            "a": [
                {
                    "b": ANYTHING,
                },
            ]
        }
        b = copy.deepcopy(a)

        b["a"][0]["b"] = "wrong"

        check_keys_match_recursive(a, b, [])

    def test_match_nested_anything_list(self):
        a = {
            "a": [
                ANYTHING,
            ]
        }
        b = copy.deepcopy(a)

        b["a"][0] = "wrong"

        check_keys_match_recursive(a, b, [])

    def test_match_ordered(self):
        """Should be able to match an ordereddict"""
        first = dict(
            a=1,
            b=2,
        )

        second = OrderedDict(
            b=2,
            a=1,
        )

        check_keys_match_recursive(first, second, [])

    def test_key_case_matters(self):
        """Make sure case of keys matters"""
        a = {
            "a": [
                {
                    "b": "val",
                },
            ]
        }
        b = copy.deepcopy(a)
        b["a"][0] = {"B": "val"}

        with pytest.raises(exceptions.KeyMismatchError):
            check_keys_match_recursive(a, b, [])

    def test_value_case_matters(self):
        """Make sure case of values matters"""
        a = {
            "a": [
                {
                    "b": "val",
                },
            ]
        }
        b = copy.deepcopy(a)
        b["a"][0]["b"] = "VAL"

        with pytest.raises(exceptions.KeyMismatchError):
            check_keys_match_recursive(a, b, [])


@pytest.fixture(name="test_yaml")
def fix_test_yaml():
    text = dedent("""
    ---
    name: Make sure server doubles number properly

    stages:
      - name: Make sure number is returned correctly
        request:
          url: http://localhost:5000/double
          json:
            is_sensitive: !bool "False"
            raw_str: !raw '{"query": "{ val1 { val2 { val3 { val4, val5 } } } }"}'
            number: !int '5'
            return_float: !bool "True"
          method: POST
          headers:
            content-type: application/json
        response:
          status_code: 200
          body:
            double: !float 10
    """)

    return text


class TestCustomTokens:
    def assert_type_value(self, test_value, expected_type, expected_value):
        assert isinstance(test_value, expected_type)
        assert test_value == expected_value

    def test_conversion(self, test_yaml):
        stages = yaml.load(test_yaml, Loader=IncludeLoader)['stages'][0]

        self.assert_type_value(stages['request']['json']['number'], int, 5)
        self.assert_type_value(
            stages['response']['body']['double'], float, 10.0)
        self.assert_type_value(
            stages['request']['json']['return_float'], bool, True)
        self.assert_type_value(
            stages['request']['json']['is_sensitive'], bool, False)
        self.assert_type_value(
            stages['request']['json']['raw_str'],
            str,
            '{{"query": "{{ val1 {{ val2 {{ val3 {{ val4, val5 }} }} }} }}"}}'
        )


class TestFormatKeys:
    def test_format_with_extention(self):
        to_format = {
            "a": {
                "$ext": {
                    "function": "random_string",
                    "extra_args": ["{number}", "{str}"],
                    "extra_kwargs": {
                        "num": "{number}"
                    }
                }
            },
            "b": {
                "$ext": {
                    "function": "os:custom_function",
                    "extra_args": ["{number}", "{str}"],
                    "extra_kwargs": {
                        "str": "{str}"
                    }
                }
            }
        }
        format_variables = {
            "number": 4,
            "str": "123"
        }

        final_value = "abcd"

        with patch("tavern.util.built_in.random_string", return_value=final_value) as pmock:
            with patch("os.custom_function", return_value=final_value, create=True) as pmock_custom:
                formatted_value = format_keys(to_format, format_variables)
                assert formatted_value["a"] == final_value
                assert formatted_value["b"] == final_value

        pmock.assert_called_with(4, "123", num=4)
        pmock_custom.assert_called_with(4, "123", str="123")

    def test_format_missing_raises(self):
        to_format = {
            "a": "{b}",
        }

        with pytest.raises(exceptions.MissingFormatError):
            format_keys(to_format, {})

    def test_format_with_built_in_import_missing_raises(self):
        to_format = {
            "a": {
                "$ext": {
                    "function": "not_exist_built_in"
                }
            }
        }
        with pytest.raises(exceptions.InvalidExtFunctionError):
            format_keys(to_format, {})

    def test_format_with_extension_import_missing_raises(self):
        to_format = {
            "a": {
                "$ext": {
                    "function": "os:not_exist"
                }
            }
        }
        with pytest.raises(exceptions.InvalidExtFunctionError):
            format_keys(to_format, {})

    def test_format_success(self):
        to_format = {
            "a1": "{b}",
            "a2": "this is {b.formatted}",
            "a3": "{b.formatted}",
            "a4": "{b.formatted_bool}",
            "a5": "this is {b.formatted_bool}",
            "a6": "this is {b}"
        }

        final_value = {
            "formatted": 1,
            "formatted_bool": True
        }

        format_variables = {
            "b": final_value
        }
        formatted_value = format_keys(to_format, format_variables)

        assert formatted_value["a1"] == final_value
        assert formatted_value["a2"] == "this is 1"
        assert formatted_value["a3"] == 1
        assert formatted_value["a4"]
        assert formatted_value["a5"] == "this is True"
        assert formatted_value["a6"] == "this is {'formatted': 1, 'formatted_bool': True}"
