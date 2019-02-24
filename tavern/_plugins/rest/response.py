import json
import traceback
import logging

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs  # type: ignore

from tavern.schemas.extensions import get_wrapped_response_function
from tavern.util.dict_util import deep_dict_merge, format_keys, recurse_set_value
from tavern.util.exceptions import TestFailError
from tavern.util.comparator_util import comparators
from tavern.response.base import BaseResponse, indent_err_text

logger = logging.getLogger(__name__)


class RestResponse(BaseResponse):

    def __init__(self, session, name, expected, test_block_config):
        # pylint: disable=unused-argument

        super(RestResponse, self).__init__()

        defaults = {
            'status_code': 200
        }

        # validate_function 只在 verify 时才使用，故而不需要先初始化
        # body = expected.get("body") or {}
        # if "$ext" in body:
        #     self.validate_function = get_wrapped_response_function(
        #         body["$ext"])
        # else:
        #     self.validate_function = None
        self.name = name
        self.expected = deep_dict_merge(defaults, expected)
        self.response = None
        self.test_block_config = test_block_config
        self.status_code = None

        # 我们有自定义的状态码，所以不需要检查状态码是否在 1xx - 5xx 之间
        # def check_code(code):
        #     if code not in _codes:
        #         logger.warning("Unexpected status code '%s'", code)

        # if isinstance(self.expected["status_code"], int):
        #     check_code(self.expected["status_code"])
        # else:
        #     for code in self.expected["status_code"]:
        #         check_code(code)

    def __str__(self):
        if self.response:
            return self.response.text.strip()
        else:
            return "<Not run yet>"

    def _verbose_log_response(self, response):
        """Verbosely log the response object, with query params etc."""

        logger.info("Response: '%s'", response)

        def log_dict_block(block, name):
            if block:
                to_log = name + ":"

                if isinstance(block, list):
                    for v in block:
                        to_log += "\n  - {}".format(v)
                elif isinstance(block, dict):
                    for k, v in block.items():
                        to_log += "\n  {}: {}".format(k, v)
                else:
                    to_log += "\n {}".format(block)
                logger.info(to_log)

        log_dict_block(response.headers, "Headers")

        try:
            log_dict_block(response.json(), "Body")
        except ValueError:
            pass

        redirect_query_params = self._get_redirect_query_params(response)
        if redirect_query_params:
            parsed_url = urlparse(response.headers["location"])
            to_path = "{0}://{1}{2}".format(*parsed_url)
            logger.debug("Redirect location: %s", to_path)
            log_dict_block(redirect_query_params,
                           "Redirect URL query parameters")

    def _get_redirect_query_params(self, response):
        """If there was a redirect header, get any query parameters from it
        """

        try:
            redirect_url = response.headers["location"]
        except KeyError as e:
            if "redirect_query_params" in self.expected.get("save", {}):
                self._adderr("Wanted to save %s, but there was no redirect url in response",
                             self.expected["save"]["redirect_query_params"], e=e)
            redirect_query_params = {}
        else:
            parsed = urlparse(redirect_url)
            qp = parsed.query
            redirect_query_params = {i: j[0] for i, j in parse_qs(qp).items()}

        return redirect_query_params

    def _check_status_code(self, status_code, body):
        expected_code = self.expected["status_code"]

        if (isinstance(expected_code, int) and status_code == expected_code) or \
                (isinstance(expected_code, list) and (status_code in expected_code)):
            logger.debug("Status code '%s' matched expected '%s'",
                         status_code, expected_code)
            return True
        else:
            if 400 <= status_code < 500:
                # special case if there was a bad request. This assumes that the
                # response would contain some kind of information as to why this
                # request was rejected.
                self._adderr("Status code was %s, expected %s:\n%s",
                             status_code, expected_code,
                             indent_err_text(json.dumps(body)),
                             )
            else:
                self._adderr("Status code was %s, expected %s",
                             status_code, expected_code)

            return False

    def verify(self, response):
        """Verify response against expected values and returns any values that
        we wanted to save for use in future requests

        There are various ways to 'validate' a block - a specific function, just
        matching values, validating a schema, etc...

        Args:
            response (requests.Response): response object

        Returns:
            dict: Any saved values

        Raises:
            TestFailError: Something went wrong with validating the response
        """
        # pylint: disable=too-many-statements

        self._verbose_log_response(response)

        self.response = response
        self.status_code = response.status_code

        try:
            body = response.json()
        except ValueError:
            body = None

        redirect_query_params = self._get_redirect_query_params(response)

        # 添加 body, headers, redirect_query_params 进入 variables 中，以保证被 format_keys 正常解析
        self.test_block_config["variables"].update(body=body)
        self.test_block_config["variables"].update(
            redirect_query_params=redirect_query_params)
        self.test_block_config["variables"].update(
            headers=response.headers)

        is_status_code_expected = self._check_status_code(
            response.status_code, body)

        # 校验 cookie 值
        expected_cookies = format_keys(self.expected.get(
            "cookies", []), self.test_block_config["variables"])

        for cookie in expected_cookies:
            if cookie not in response.cookies:
                self._adderr("No cookie named '%s' in response", cookie)

        # 不需要单独验证
        # if self.validate_function:
        #     try:
        #         self.validate_function(response)
        #     except Exception as e:  # pylint: disable=broad-except
        #         self._adderr("Error calling validate function '%s':\n%s",
        #                      self.validate_function.func,
        #                      indent_err_text(traceback.format_exc()),
        #                      e=e)

        # Get any keys to save
        saved = {}

        if is_status_code_expected:
            if "save" in self.expected:
                saved = self._save_value(self.expected["save"])

            # Do Validation
            if "validate" in self.expected:
                self._validate_block(self.expected["validate"])

        if self.errors:
            raise TestFailError("Test '{:s}' failed:\n{:s}".format(
                self.name, self._str_errors()), failures=self.errors)

        # save 和 validate 完成后，需要清楚 variables 中的 body,headers,redirect_query_params
        self.test_block_config["variables"].pop("headers")
        self.test_block_config["variables"].pop("body")
        self.test_block_config["variables"].pop("redirect_query_params")

        return saved

    def _validate_block(self, validate_block):
        """Validate response
        """
        for validator in validate_block:
            for key, validator_args in validator.items():
                try:
                    formatted_validate_args = format_keys(
                        validator_args, self.test_block_config["variables"])
                except Exception as e:  # pylint: disable=broad-except
                    self._adderr(
                        "Format validate args %s for '%s' faild",
                        validator_args,
                        key,
                        e=e
                    )
                else:
                    if key == "$ext":
                        validate_fn = get_wrapped_response_function(
                            formatted_validate_args)
                        try:
                            validate_fn(self.response)
                        except Exception as e:  # pylint: disable=broad-except
                            self._adderr("Error calling validate function '%s':\n%s",
                                         validate_fn.func,
                                         indent_err_text(
                                             traceback.format_exc()),
                                         e=e)
                    else:
                        try:
                            comparator = comparators.get_comparator(key)
                        except Exception as e:  # pylint: disable=broad-except
                            self._adderr("Error getting comparator function '%s'".format,
                                         key,
                                         e=e
                                         )
                        else:
                            kwargs = {}
                            if len(formatted_validate_args) > 2:
                                kwargs = formatted_validate_args.pop()
                            try:
                                comparator(*formatted_validate_args, **kwargs)
                            except Exception as e:  # pylint: disable=broad-except
                                self._adderr("Error calling comparator function '%s':\n%s",
                                             key,
                                             indent_err_text(
                                                 traceback.format_exc()),
                                             e=e
                                             )

    def _save_value(self, save_block):
        """Save a value in the response for use in future tests

        Args:
            to_check (dict): An element of the response from which the given key
                is extracted
            key (str): Key to use

        Returns:
            dict: dictionary of save_name: value, where save_name is the key we
                wanted to save this value as
        """
        saved = {}

        for save_as, joined_key in save_block.items():
            try:
                logger.debug("start format save key:%s", joined_key)
                val = format_keys(
                    joined_key, self.test_block_config["variables"])
            except Exception as e:  # pylint: disable=broad-except
                self._adderr(
                    "Format saved value %s for '%s' faild",
                    joined_key,
                    save_as,
                    e=e
                )
            else:
                if save_as == "$ext":
                    ext_fn = get_wrapped_response_function(val)
                    try:
                        to_save = ext_fn(self.response)
                    except Exception as e:  # pylint: disable=broad-except
                        self._adderr("Error calling save function '%s':\n%s",
                                     ext_fn.func,
                                     indent_err_text(traceback.format_exc()),
                                     e=e)
                    else:
                        if isinstance(to_save, dict):
                            saved.update(to_save)
                        elif to_save is not None:
                            self._adderr(
                                "Unexpected return value '%s' from $ext save function")
                else:
                    split_keys = save_as.split(".")
                    try:
                        recurse_set_value(saved, split_keys, val)
                    except Exception as e:  # pylint: disable=broad-except
                        self._adderr(
                            "Set value to '%s' failed",
                            save_as,
                            e=e
                        )

        return saved
