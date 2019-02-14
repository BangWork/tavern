import json
import uuid
import os
from mock import patch, Mock, MagicMock
from copy import deepcopy
from box import Box

import pytest
import requests
import paho.mqtt.client as paho

from tavern._plugins.mqtt.client import MQTTClient
from tavern.core import run_test, resolve_spec
from tavern.util import exceptions


@pytest.fixture(name="fulltest")
def fix_example_test():
    spec = {
        "name": "A test with a single stage",
        "stages": [
            {
                "name": "test",
                "description": "step 1",
                "request": {
                    "url": "http://www.google.com",
                    "method": "GET",
                },
                "response": {
                    "status_code": 200,
                    "validate": [{
                        "eq": ["{body}", {"key": "value"}]
                    }, {
                        "eq": ["{headers.content-type}", "application/json"]
                    }]
                }
            }
        ]
    }

    return spec


@pytest.fixture(name="mockargs")
def fix_mock_response_args(fulltest):
    response = fulltest["stages"][0]["response"]
    content = {"key": "value"}

    args = {
        "spec": requests.Response,
        "content": json.dumps(content).encode("utf8"),
        "status_code": response["status_code"],
        "json": lambda: content,
        "headers": {"content-type": "application/json"},
    }

    return args


class TestRunStages:

    def test_success(self, fulltest, mockargs, includes):
        """Successful test
        """

        mock_response = Mock(**mockargs)

        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_response) as pmock:
            run_test("heif", fulltest, includes)

        assert pmock.called

    def test_invalid_code(self, fulltest, mockargs, includes):
        """Wrong status code
        """

        mockargs["status_code"] = 400

        mock_response = Mock(**mockargs)

        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_response) as pmock:
            with pytest.raises(exceptions.TestFailError):
                run_test("heif", fulltest, includes)

        assert pmock.called

    def test_invalid_body(self, fulltest, mockargs, includes):
        """Wrong body returned
        """

        mockargs["json"] = lambda: {"wrong": "thing"}

        mock_response = Mock(**mockargs)

        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_response) as pmock:
            with pytest.raises(exceptions.TestFailError):
                run_test("heif", fulltest, includes)

        assert pmock.called

    def test_invalid_headers(self, fulltest, mockargs, includes):
        """Wrong headers
        """

        mockargs["headers"] = {
            "content-type": "application/x-www-url-formencoded"}

        mock_response = Mock(**mockargs)

        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_response) as pmock:
            with pytest.raises(exceptions.TestFailError):
                run_test("heif", fulltest, includes)

        assert pmock.called

    def test_external_stage(self, fulltest, mockargs, includes):
        """ Successfully load and run stage ref from the includes
        """

        mock_response = Mock(**mockargs)

        newtest = deepcopy(fulltest)
        newtest["includes"] = [deepcopy(includes)]
        newtest["stages"].insert(
            0, {"ref": "my_external_stage"})
        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_response) as pmock:
            run_test("heif", newtest, includes)

        assert pmock.called

        # We expect 2 calls, first to bing (external stage),
        # then google (part of fulltest)
        assert len(pmock.call_args_list) == 2
        args, kwargs = pmock.call_args_list[0]
        assert kwargs["url"] == "http://www.bing.com"
        args, kwargs = pmock.call_args_list[1]
        assert kwargs["url"] == "http://www.google.com"

    def test_recurse_external_stage(self, fulltest, mockargs, includes):
        """ Successfully load and run stage ref from the includes
        """

        mock_response = Mock(**mockargs)

        newtest = deepcopy(fulltest)
        newtest["includes"] = [{
            "includes": [deepcopy(includes)],
            "variable":{
                "new_prefix": "{request.prefix}.abc"
            },
            "stages": [{
                "id": "new_ref_stage",
                "ref": "my_external_stage"
            }]
        }]
        newtest["stages"].insert(
            0, {"ref": "new_ref_stage"})
        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_response) as pmock:
            run_test("heif", newtest, includes)

        assert pmock.called

        # We expect 2 calls, first to bing (external stage),
        # then google (part of fulltest)
        assert len(pmock.call_args_list) == 2
        args, kwargs = pmock.call_args_list[0]
        assert kwargs["url"] == "http://www.bing.com"
        args, kwargs = pmock.call_args_list[1]
        assert kwargs["url"] == "http://www.google.com"


class TestRetry:

    def test_repeats_twice_and_succeeds(self, fulltest, mockargs, includes):
        fulltest["stages"][0]["max_retries"] = 1
        failed_mockargs = deepcopy(mockargs)
        failed_mockargs['status_code'] = 400

        mock_responses = [
            Mock(**failed_mockargs),
            Mock(**mockargs),
        ]

        with patch("tavern._plugins.rest.request.requests.Session.request", side_effect=mock_responses) as pmock:
            run_test("heif", fulltest, includes)

        assert pmock.call_count == 2

    def test_repeats_twice_and_fails(self, fulltest, mockargs, includes):
        fulltest["stages"][0]["max_retries"] = 1
        mockargs['status_code'] = 400
        mock_response = Mock(**mockargs)

        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_response) as pmock:
            with pytest.raises(exceptions.TestFailError):
                run_test("heif", fulltest, includes)

        assert pmock.call_count == 2

    def test_run_once(self, fulltest, mockargs, includes):
        mock_responses = Mock(**mockargs)

        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_responses) as pmock:
            run_test("heif", fulltest, includes)

        assert pmock.call_count == 1


class TestDelay:

    def test_sleep_before(self, fulltest, mockargs, includes):
        """Should sleep with delay_before in stage spec"""

        fulltest["stages"][0]["delay_before"] = 2

        mock_response = Mock(**mockargs)

        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_response) as pmock:
            with patch("tavern.util.delay.time.sleep") as smock:
                run_test("heif", fulltest, includes)

        assert pmock.called
        smock.assert_called_with(2)

    def test_sleep_after(self, fulltest, mockargs, includes):
        """Should sleep with delay_after in stage spec"""

        fulltest["stages"][0]["delay_after"] = 2

        mock_response = Mock(**mockargs)

        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_response) as pmock:
            with patch("tavern.util.delay.time.sleep") as smock:
                run_test("heif", fulltest, includes)

        assert pmock.called
        smock.assert_called_with(2)


class TestTavernMetaFormat:

    def test_format_env_keys(self, fulltest, mockargs, includes):
        """Should be able to get variables from the environment and use them in
        test responses"""

        env_key = "SPECIAL_CI_MAGIC_COMMIT_TAG"

        fulltest["stages"][0]["request"]["params"] = {
            "a_format_key": "{tavern.env_vars.%s}" % env_key}

        mock_response = Mock(**mockargs)

        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_response) as pmock:
            with patch.dict(os.environ, {env_key: "bleuihg"}):
                includes["variables"]["tavern"] = Box({
                    "env_vars": dict(os.environ),
                })
                run_test("heif", fulltest, includes)
                includes["variables"].pop("tavern")

        assert pmock.called

    def test_format_env_keys_missing_failure(self, fulltest, mockargs, includes):
        """Fails if key is not present"""

        env_key = "SPECIAL_CI_MAGIC_COMMIT_TAG"

        fulltest["stages"][0]["request"]["params"] = {
            "a_format_key": "{tavern.env_vars.%s}" % env_key}

        with pytest.raises(exceptions.MissingFormatError):
            includes["variables"]["tavern"] = Box({
                "env_vars": dict(os.environ),
            })
            run_test("heif", fulltest, includes)
            includes["variables"].pop("tavern")


class TestFormatRequestVars:

    @pytest.mark.parametrize("request_key", (
        "params",
        "json",
        "headers",
    ))
    def test_format_request_var_dict(self, fulltest, mockargs, includes, request_key):
        """Variables from request should be available to format in response"""

        sent_value = str(uuid.uuid4())

        fulltest["stages"][0]["request"]["method"] = "POST"
        fulltest["stages"][0]["request"][request_key] = {
            "a_format_key": sent_value}

        if request_key == "json" or request_key == "params":
            resp_key = "body"
            mockargs[resp_key] = lambda: {"returned": sent_value}
        else:
            resp_key = request_key
            mockargs[resp_key] = {"returned": sent_value}

        fulltest["stages"][0]["response"]["validate"] = [{
            "eq": [{"returned": "{request.%s}" % request_key}, {"returned": "{request.%s}" % request_key}]
        }]

        mock_response = Mock(**mockargs)
        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_response) as pmock:
            run_test("heif", fulltest, includes)

        assert pmock.called

    @pytest.mark.parametrize("request_key", (
        "url",
        "method",
    ))
    def test_format_request_var_value(self, fulltest, mockargs, includes, request_key):
        """Variables from request should be available to format in response"""

        sent_value = str(uuid.uuid4())

        fulltest["stages"][0]["request"]["method"] = "POST"
        fulltest["stages"][0]["request"][request_key] = sent_value

        mockargs[request_key] = {"returned": sent_value}

        fulltest["stages"][0]["response"]["validate"] = [{
            "eq": [{"returned": "{request.%s}" % request_key}, {"returned": "{request.%s}" % request_key}]
        }]

        mock_response = Mock(**mockargs)

        with patch("tavern._plugins.rest.request.requests.Session.request", return_value=mock_response) as pmock:
            run_test("heif", fulltest, includes)

        assert pmock.called


class TestFormatMQTTVarsJson:
    """Test that formatting request vars from mqtt works as well, with json payload
    """

    @pytest.fixture(name="fulltest")
    def fix_mqtt_publish_test(self):
        spec = {
            "name": "An mqtt test with a single stage",
            "mqtt": {
                "connect": "localhost",
            },
            "stages": [
                {
                    "id": "test",
                    "name": "step 1",
                    "mqtt_publish": {
                        "topic": "/abc/123",
                        "json": {
                            "message": str(uuid.uuid4()),
                        }
                    },
                    "mqtt_response": {
                        "topic": "{request.topic}",
                        "json": {
                            "echo": "{request.json.message}",
                        },
                    }
                }
            ]
        }

        return spec

    def test_format_request_var_dict(self, fulltest, includes):
        """Variables from request should be available to format in response -
        this is the original keys in the input file, NOT the formatted ones
        where 'json' is converted to 'payload' in the actual MQTT publish"""

        stage = fulltest["stages"][0]
        sent = stage["mqtt_publish"]["json"]

        mockargs = {
            "spec": paho.MQTTMessage,
            "payload": json.dumps({"echo": sent["message"]}).encode("utf8"),
            "topic": stage["mqtt_publish"]["topic"],
        }
        mock_response = Mock(**mockargs)

        fake_client = MagicMock(
            spec=MQTTClient,
            message_received=Mock(return_value=mock_response),
        )

        with patch("tavern._plugins.mqtt.client.paho.Client", fake_client), \
                patch("tavern.core.get_extra_sessions", return_value={"paho-mqtt": fake_client}) as pmock:
            run_test("heif", fulltest, includes)

        assert pmock.called


class TestFormatMQTTVarsPlain:
    """Test that formatting request vars from mqtt works as well, with normal payload
    """

    @pytest.fixture(name="fulltest")
    def fix_mqtt_publish_test(self):
        spec = {
            "name": "An mqtt test with a single stage",
            "mqtt": {
                "connect": "localhost",
            },
            "stages": [
                {
                    "id": "test",
                    "name": "step 1",
                    "mqtt_publish": {
                        "topic": "/abc/123",
                        "payload": "hello",
                    },
                    "mqtt_response": {
                        "topic": "{request.topic}",
                        "payload": "{request.payload}",
                    }
                }
            ]
        }

        return spec

    def test_format_request_var_value(self, fulltest, includes):
        """Same as above but with plain keys"""
        stage = fulltest["stages"][0]
        sent = stage["mqtt_publish"]["payload"]

        mockargs = {
            "spec": paho.MQTTMessage,
            "payload": sent.encode("utf8"),
            "topic": stage["mqtt_publish"]["topic"],
        }
        mock_response = Mock(**mockargs)

        fake_client = MagicMock(
            spec=MQTTClient,
            message_received=Mock(return_value=mock_response),
        )

        with patch("tavern._plugins.mqtt.client.paho.Client", fake_client), \
                patch("tavern.core.get_extra_sessions", return_value={"paho-mqtt": fake_client}) as pmock:
            run_test("heif", fulltest, includes)

        assert pmock.called


class TestResolveSpec:
    """Test resolve spec"""

    def test_resolve_spec(self):
        """ test resolve spec
            after resolve stage, will only format the keys in variables,marks,usefixtures
        """
        base_spec = {
            "name": "base spec",
            "stages": [{
                "id": "base_stage",
                "name": "base stage",
                "request": {
                    "url": "www.google.com",
                    "json": {
                        "test": "{first_var}"
                    }
                }
            }]
        }

        ref_spec = {
            "includes": [base_spec],
            "stages": [{
                "ref": "base_stage",
                "id": "ref_stage",
                "name": "reference stage",
                "request": {
                    "json": {
                        "test2": "{second_var}"
                    }
                }
            }]
        }

        final_spec = {
            "includes": [ref_spec],
            "stages": [{
                "ref": "ref_stage"
            }]
        }
        final_stages = resolve_spec(final_spec)

        assert list(final_stages.keys()) == ["base_stage", "ref_stage"]
        assert final_stages["ref_stage"]["request"]['json'] == {
            "test": "{first_var}", "test2": "{second_var}"}
