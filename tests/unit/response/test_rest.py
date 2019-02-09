import pytest
from mock import Mock, patch

from tavern._plugins.rest.response import RestResponse
from tavern.util.loader import ANYTHING
from tavern.util import exceptions


@pytest.fixture(name="example_schema")
def fix_example_schema():
    spec = {
        "status_code": 302,
        "validate": [
            {"eq": ["{headers.Content-Type}", "application/json"]},
            {"eq": ["{body.a_thing}", "authorization_code"]},
            {"eq": ["{body.code}", "abc123"]}
        ]
    }

    return spec.copy()


@pytest.fixture(name="example_response")
def fix_example_response():
    spec = {
        "status_code": 302,
        "headers": {
            "Content-Type": "application/json",
            "location": "www.google.com?search=breadsticks",
        },
        "body": {
            "a_thing":  "authorization_code",
            "code":  "abc123",
        },
    }

    return spec.copy()


@pytest.fixture(name='nested_response')
def fix_nested_response():
    # https://github.com/taverntesting/tavern/issues/45
    spec = {
        "status_code": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": {
            "users": [
                {
                    "u": {
                        "user_id": "def456"
                    }
                }
            ]
        }
    }

    return spec.copy()


@pytest.fixture(name='nested_schema')
def fix_nested_schema():
    # https://github.com/taverntesting/tavern/issues/45
    spec = {
        "status_code": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "validate": [
            {
                "eq": [
                    "{body}",
                    {
                        "users": [
                            {
                                "u": {
                                    "user_id": "{code}"
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }

    return spec.copy()


class TestSave:

    def test_save_body(self, example_response, example_schema, includes):
        """Save a key from the body into the right name
        """
        example_schema["save"] = {"test_code": "{body.code}"}
        includes["variables"]["body"] = example_response["body"]
        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        saved = r._save_value(example_schema["save"])
        includes["variables"].pop("body")
        assert saved == {"test_code": example_response["body"]["code"]}

    def test_save_body_nested(self, example_response, example_schema, includes):
        """Save a key from the body into the right name
        """
        example_response["body"]["nested"] = {
            "subthing": "blah"
        }
        example_schema["save"] = {
            "test_nested_thing": "{body.nested.subthing}"
        }
        includes["variables"]["body"] = example_response["body"]
        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        saved = r._save_value(example_schema["save"])
        includes["variables"].pop("body")

        assert saved == {
            "test_nested_thing": example_response["body"]["nested"]["subthing"]}

    def test_save_body_nested_list(self, example_response, example_schema, includes):
        """Save a key from the body into the right name
        """
        example_response["body"]["nested"] = {
            "subthing": [
                "abc",
                "def",
            ]
        }
        example_schema["save"] = {
            "test_nested_thing": "{body.nested.subthing.0}"
        }
        includes["variables"]["body"] = example_response["body"]
        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        saved = r._save_value(example_schema["save"])
        includes["variables"].pop("body")

        assert saved == {
            "test_nested_thing": example_response["body"]["nested"]["subthing"][0]}

    def test_save_header(self, example_response, example_schema, includes):
        """Save a key from the headers into the right name
        """
        example_schema["save"] = {"next_location": "{headers.location}"}
        includes["variables"]["headers"] = example_response["headers"]
        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        saved = r._save_value(example_schema["save"])
        includes["variables"].pop("headers")
        assert saved == {
            "next_location": example_response["headers"]["location"]}

    def test_save_redirect_query_param(self, example_schema, includes):
        """Save a key from the query parameters of the redirect location
        """
        example_schema["save"] = {
            "test_search": "{redirect_query_params.search}"}
        includes["variables"]["redirect_query_params"] = {
            "search": "breadsticks"}
        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        saved = r._save_value(example_schema["save"])
        includes["variables"].pop("redirect_query_params")
        assert saved == {"test_search": "breadsticks"}

    @pytest.mark.parametrize("save_from", (
        "body",
        "headers",
        "redirect_query_params",
    ))
    def test_bad_save(self, save_from, example_schema, includes):
        key = "{}.123".format(save_from)

        example_schema["save"] = {"abc": "{%s}" % key}

        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        saved = r._save_value(example_schema["save"])

        assert not saved

        assert r.errors


class TestValidate:

    def test_simple_validate_body(self, example_response, example_schema, includes):
        """Make sure a simple value comparison works
        """
        includes["variables"]["body"] = example_response["body"]
        validate_block = [
            {"eq": ["{body}", example_response["body"]]}
        ]

        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        r._validate_block(validate_block)
        includes["variables"].pop("body")
        assert not r.errors

    def test_validate_list_body(self, example_response, example_schema, includes):
        """Make sure a list response can be validated
        """

        example_response["body"] = ["a", 1, "b"]

        r = RestResponse(Mock(), "Test 1", example_schema, includes)
        includes["variables"]["body"] = example_response["body"]
        validate_block = [
            {"eq": ["{body}", example_response["body"]]}
        ]

        r._validate_block(validate_block)

        includes["variables"].pop("body")
        assert not r.errors

    def test_validate_list_body_wrong_order(self, example_response, example_schema, includes):
        """Order of list items matters
        """

        example_response["body"] = ["a", 1, "b"]

        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        includes["variables"]["body"] = example_response["body"]
        validate_block = [
            {"eq": ["{body}", example_response["body"][::-1]]}
        ]

        r._validate_block(validate_block)
        includes["variables"].pop("body")
        assert r.errors

    def test_validate_nested_body(self, example_response, example_schema, includes):
        """Make sure a nested value comparison works
        """

        example_response["body"]["nested"] = {"subthing": "blah"}

        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        includes["variables"]["body"] = example_response["body"]
        validate_block = [
            {"eq": ["{body}", example_response["body"]]}
        ]

        r._validate_block(validate_block)
        includes["variables"].pop("body")
        assert not r.errors

    def test_simple_validate_headers(self, example_response, example_schema, includes):
        """Make sure a simple value comparison works
        """

        r = RestResponse(Mock(), "Test 1", example_schema, includes)
        includes["variables"]["headers"] = example_response["headers"]
        validate_block = [
            {"eq": ["{headers}", example_response["headers"]]}
        ]

        r._validate_block(validate_block)
        includes["variables"].pop("headers")
        assert not r.errors

    def test_simple_validate_redirect_query_params(self, example_response, example_schema, includes):
        """Make sure a simple value comparison works
        """

        r = RestResponse(Mock(), "Test 1", example_schema, includes)
        includes["variables"]["redirect_query_params"] = {
            "search": "breadsticks"}
        validate_block = [
            {"eq": ["{redirect_query_params}", {"search": "breadsticks"}]}
        ]
        r._validate_block(validate_block)
        includes["variables"].pop("redirect_query_params")
        assert not r.errors

    def test_validate_missing_list_key(self, example_response, example_schema, includes):
        """If we expect 4 items and 3 were returned, catch error"""

        example_response["body"] = ["a", 1, "b", "c"]
        bad_expected = example_response["body"][:-1]

        r = RestResponse(Mock(), "Test 1", example_schema, includes)
        includes["variables"]["body"] = example_response["body"]
        validate_block = [
            {"eq": ["{body}", bad_expected]}
        ]
        r._validate_block(validate_block)
        includes["variables"].pop("body")
        assert r.errors

    def test_validate_wrong_list_dict(self, example_response, example_schema, includes):
        """We expected a list, but we got a dict in the response"""

        example_response["body"] = ["a", 1, "b", "c"]
        bad_expected = {"a": "b"}
        includes["variables"]["body"] = example_response["body"]
        r = RestResponse(Mock(), "Test 1", example_schema, includes)
        validate_block = [
            {"eq": ["{body}", bad_expected]}
        ]
        r._validate_block(validate_block)
        includes["variables"].pop("body")
        assert r.errors

    def test_validate_wrong_dict_list(self, example_response, example_schema, includes):
        """We expected a dict, but we got a list in the response"""

        example_response["body"] = {"a": "b"}
        bad_expected = ["a", "b", "c"]
        includes["variables"]["body"] = example_response["body"]
        r = RestResponse(Mock(), "Test 1", example_schema, includes)
        validate_block = [
            {"eq": ["{body}", bad_expected]}
        ]
        r._validate_block(validate_block)
        includes["variables"].pop("body")
        assert r.errors


class TestMatchStatusCodes:

    def test_validate_single_status_code_passes(self, example_schema, includes):
        """single status code match"""

        example_schema["status_code"] = 100

        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        r._check_status_code(100, {})

        assert not r.errors

    def test_validate_single_status_code_incorrect(self, example_schema, includes):
        """single status code mismatch"""

        example_schema["status_code"] = 100

        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        r._check_status_code(102, {})

        assert r.errors

    def test_validate_multiple_status_codes_passes(self, example_schema, includes):
        """Check it can match mutliple status codes"""

        example_schema["status_code"] = [
            100,
            200,
            300,
        ]

        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        r._check_status_code(100, {})

        assert not r.errors

    def test_validate_multiple_status_codes_missing(self, example_schema, includes):
        """Status code was not in list"""

        example_schema["status_code"] = [
            100,
            200,
            300,
        ]

        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        r._check_status_code(103, {})

        assert r.errors


class TestNestedValidate:

    def test_validate_nested_anything(self, example_response, example_schema, includes):
        """Check that nested 'anything' comparisons work

        This is a bit hacky because we're directly checking the ANYTHING
        comparison - need to add an integration test too
        """

        example_response["body"] = {
            "nested": {
                "subthing": "blabla",
            }
        }
        includes["variables"]["body"] = example_response["body"]
        validate_block = [
            {"eq": ["{body.nested}", {"subthing": ANYTHING}]}
        ]

        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        r._validate_block(validate_block)
        includes["variables"].pop("body")
        assert not r.errors

    def test_validate_with_strict_key_check(self, example_response, example_schema, includes):
        example_response["body"] = {
            "nested": {
                "subthing": "blabla",
            }
        }
        includes["variables"]["body"] = example_response["body"]
        validate_block = [
            {"eq": ["{body.nested.subthing}", ANYTHING, {"strict": True}]}
        ]

        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        with patch("tavern.util.built_in.equals", return_value=True) as pmock:
            r._validate_block(validate_block)

        pmock.assert_called_with("blabla", ANYTHING, strict=True)
        includes["variables"].pop("body")
        assert not r.errors


class TestFull:

    def test_validate_and_save(self, example_response, example_schema, includes):
        """Test full verification + return saved values
        """
        example_schema["save"] = {"test_code": "{body.code}"}
        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        class FakeResponse:
            headers = example_response["headers"]
            content = "test".encode("utf8")

            def json(self):
                return example_response["body"]
            status_code = example_response["status_code"]

        saved = r.verify(FakeResponse())

        assert saved == {"test_code": example_response["body"]["code"]}

    def test_incorrect_status_code(self, example_response, example_schema, includes):
        """Test full verification + return saved values
        """
        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        class FakeResponse:
            headers = example_response["headers"]
            content = "test".encode("utf8")

            def json(self):
                return example_response["body"]
            status_code = 400

        with pytest.raises(exceptions.TestFailError):
            r.verify(FakeResponse())

        assert r.errors

    def test_saved_value_in_validate(self, nested_response, nested_schema,
                                     includes):
        r = RestResponse(Mock(), "Test 1", nested_schema, includes)

        class FakeResponse:
            headers = nested_response["headers"]
            content = "test".encode("utf8")

            def json(self):
                return nested_response["body"]
            status_code = nested_response["status_code"]

        r.verify(FakeResponse())

    @pytest.mark.parametrize('value', [1, 'some', False, None])
    def test_validate_single_value_response(self, example_response, example_schema, includes,
                                            value):
        """Check validating single value response (string, int, etc)."""
        del example_response['body']

        example_schema["validate"] = [
            {"eq": ["{body}", value]}
        ]

        r = RestResponse(Mock(), "Test 1", example_schema, includes)

        class FakeResponse:
            headers = example_response["headers"]
            content = "test".encode("utf8")

            def json(self):
                return value
            status_code = example_response["status_code"]

        r.verify(FakeResponse())
