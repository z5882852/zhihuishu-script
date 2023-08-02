import json
import re
import execjs
import requests
from utils import path as file_path
from execjs import _runner_sources

# 本地nodejs环境
local_node_runtime = execjs.ExternalRuntime(
    name="Node.js (V8) local",
    command='',
    encoding='UTF-8',
    runner_source=_runner_sources.Node
)
local_node_runtime._binary_cache = [file_path.NODEJS_PATH]
local_node_runtime._available = True
execjs.register('local_node', local_node_runtime)


def get_ctx(path):
    """
    获取js对象
    :param path: js文件路径
    :return:
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    ctx = execjs.get('local_node').compile(content)
    # ctx = execjs.compile(content)
    return ctx


def get_fp_callback():
    """
    获取fp、callback参数
    :return: fp, callback
    """
    ctx = get_ctx(file_path.CAPTCHA_FP_JS_PATH)
    # ctx = get_ctx("js/fp.js")
    fp = ctx.call('get_fp')
    callback = ctx.call('get_callback')
    return fp, callback


def get_secure_captcha(validate, fp, zoneId):
    """
    获取加密后的验证码
    :param validate: 验证成功返回的 validate
    :param fp: fingerprint
    :param zoneId: 一般是CN31
    :return: 加密后的验证码
    """
    ctx = get_ctx(file_path.CAPTCHA_SC_JS_PATH)
    # ctx = get_ctx("js/secureCaptcha.js")
    return ctx.call('getSecureCaptcha', validate, fp, zoneId)


def get_check_data(token, x, y):
    ctx = get_ctx(file_path.CAPTCHA_SC_JS_PATH)
    # ctx = get_ctx("js/secureCaptcha.js")
    return ctx.call('get_data', token, x, y)


class crypto_params:
    def __init__(self):
        self.ctx = get_ctx(file_path.CAPTCHA_CB_JS_PATH)
        # self.ctx = get_ctx("js/cb.js")

    def get_cb(self):
        return self.ctx.call('cb')

    def get_data(self, token, trace, left):
        return self.ctx.call('get_data', token, trace, left)


class SpaceInference:
    def __init__(self, captcha_id=''):
        """
        获取网易易盾的validate
        :param captcha_id: 网易易盾的CAPTCHA_ID
        """
        self.captcha_id = captcha_id
        self.captcha_data = {
            'v': 'e2891084',
            'version': '2.21.5',
            'type': '2',
        }
        self.crypto_param = crypto_params()
        self.token = None
        self.result = None
        self.secure_captcha = None
        self.fp = ""

    @staticmethod
    def __headers__():
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Host': 'c.dun.163yun.com',
            'Referer': '',
            'Pragma': 'no-cache',
            'Proxy-Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        }
        return headers

    def get_captcha(self, actoken=None):
        # 获取fp和callback
        self.fp, callback = get_fp_callback()
        data = {
            "id": self.captcha_id,
            "fp": self.fp,
            "https": "true",
            "type": self.captcha_data.get('type', '2'),
            "version": self.captcha_data.get('version', '2.21.5'),
            "dpr": "1",
            "dev": "1",
            "cb": self.crypto_param.get_cb(),
            "ipv6": "false",
            "runEnv": "10",
            "group": "",
            "scene": "",
            "width": "320",
            "token": "",
            "referer": "",
            "callback": callback
        }
        r = requests.get('https://c.dun.163.com/api/v2/get', params=data, headers=self.__headers__(), timeout=2)
        data_ = json.loads(re.findall('.*?\((.*?)\);', r.text)[0])
        self.token = data_.get('data', {}).get('token', None)
        return data_

    def check(self, x, y):
        """提交验证部分"""
        if not self.token:
            return False
        data = get_check_data(self.token, x, y)
        params = {
            "referer": "https://studyvideoh5.zhihuishu.com/stuStudy",
            "zoneId": "CN31",
            "id": self.captcha_id,
            "token": self.token,
            "acToken": "undefined",
            "data": data,
            "width": "320",
            "type": self.captcha_data.get('type', '2'),
            "version": self.captcha_data.get('version', '2.21.5'),
            "cb": self.crypto_param.get_cb(),
            "extraData": "",
            "bf": "0",
            "runEnv": "10",
            "sdkVersion": "undefined",
            "callback": "__JSONP_48mk47t_1"
        }
        r = requests.get('https://c.dun.163.com/api/v2/check', headers=self.__headers__(), params=params)
        data = r.text[18:-2]
        self.result = json.loads(data).get("data", {})
        if self.result.get('result'):
            self.secure_captcha = get_secure_captcha(
                self.result.get('validate'),
                self.fp,
                self.result.get('zoneId')
            )
