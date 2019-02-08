import logging

import requests
from future.utils import raise_from

from tavern.util.dict_util import format_keys
from tavern.plugins import PluginHelperBase
from tavern.util import exceptions

from .request import RestRequest
from .response import RestResponse


logger = logging.getLogger(__name__)


class TavernRestPlugin(PluginHelperBase):
    session_type = requests.Session

    request_type = RestRequest
    request_block_name = "request"

    @staticmethod
    def get_expected_from_request(stage, test_block_config, session):
        # pylint: disable=unused-argument
        try:
            r_expected = stage["response"]
        except KeyError as e:
            logger.error(
                "Need a 'response' block if a 'request' is being sent")
            raise_from(exceptions.MissingSettingsError, e)
        # 此处原本是为了在初始化 response 的时候，就已经用 variables 去替换模版。但其实在 verify 里做更好
        # 因为我们的定制化代码里，让 format_keys 支持了每一个参数都可以使用 $ext 去获取其值
        # 故而此处不需要预先进行转换了
        # f_expected = format_keys(r_expected, test_block_config["variables"])
        return r_expected

    verifier_type = RestResponse
    response_block_name = "response"
