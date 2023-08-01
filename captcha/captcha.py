import json
import re
import math
import random
import execjs
import requests

from urllib import request
import numpy as np

from captcha.gap import get_gap
from utils import path as file_path


def get_track(space):
    """
    获取轨迹
    :param space:
    :return:
    """
    x = [0, 0]
    y = [0, 0, 0]
    z = [0]
    count = np.linspace(-math.pi / 2, math.pi / 2, random.randrange(20, 30))
    func = list(map(math.sin, count))
    nx = [i + 1 for i in func]
    add = random.randrange(10, 15)
    sadd = space + add
    x.extend(list(map(lambda x: x * (sadd / 2), nx)))
    x.extend(np.linspace(sadd, space, 3 if add > 12 else 2))
    x = [math.floor(i) for i in x]
    for i in range(len(x) - 2):
        if y[-1] < 30:
            y.append(y[-1] + random.choice([0, 0, 1, 1, 2, 2, 1, 2, 0, 0, 3, 3]))
        else:
            y.append(y[-1] + random.choice([0, 0, -1, -1, -2, -2, -1, -2, 0, 0, -3, -3]))
    for i in range(len(x) - 1):
        z.append((z[-1] // 100 * 100) + 100 + random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2]))
    return list(map(list, zip(x, y, z)))


def get_ctx(path):
    """
    获取js对象
    :param path: js文件路径
    :return:
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    ctx = execjs.compile(content)
    return ctx


def get_fp_callback():
    """
    获取fp、callback参数
    :return: fp, callback
    """
    ctx = get_ctx(file_path.CAPTCHA_FP_JS_PATH)
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
    return ctx.call('getSecureCaptcha', validate, fp, zoneId)


class crypto_params:
    def __init__(self):
        self.ctx = get_ctx(file_path.CAPTCHA_CB_JS_PATH)

    def get_cb(self):
        return self.ctx.call('cb')

    def get_data(self, token, trace, left):
        return self.ctx.call('get_data', token, trace, left)


class yidun:
    def __init__(self, captcha_id=''):
        """
        获取网易易盾的validate
        :param id: 网易易盾的CAPTCHA_ID
        """
        self.captcha_id = captcha_id
        self.captcha_data = {
            'v': 'e2891084',
            'version': '2.21.5',
            'type': '2',
        }
        self.result = None
        self.secure_captcha = None
        self.counter = 0
        self.fp = ""
        self.validate()

    def get_actoken_median(self, ctx, rdtm):
        """
        :param ctx: execjs处理得actoken.js对象
        :param rdtm:js里时间相关得值md5结果
        :return:did是d请求得第二个字符串
        """
        headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Length": "762",
            "Content-type": "application/x-www-form-urlencoded",
            "Host": "ac.dun.163yun.com",
            "Origin": "https://dun.163.com",
            "Pragma": "no-cache",
            "Referer": "",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"
        }
        param = ctx.call('request_d')
        data = {
            'd': param,
            'v': self.captcha_data.get('v', 'e2891084'),
            'cb': '__wmjsonp_6d6c02f'
        }
        r = requests.post('https://ac.dun.163yun.com/v3/d', data=data, headers=headers)
        did = re.findall('"(.*?)"', r.text)[1]
        tid = re.findall('"(.*?)"', r.text)[0]
        param = ctx.call('verify_b', rdtm, tid, did)
        data = {
            'd': param,
            'v': self.captcha_data.get('v', 'e2891084'),
            'cb': '__wmjsonp_6d6c02f'
        }

        # 激活rdtm然后给actoken加密
        r = requests.post('https://ac.dun.163yun.com/v3/b', data=data, headers=headers)
        return did

    def validate(self, actoken=None):
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
        # 获取fp和callback
        self.fp, callback = get_fp_callback()

        crypto_param = crypto_params()
        cb = crypto_param.get_cb()

        data = {
            "id": self.captcha_id,
            "fp": self.fp,
            "https": "true",
            "type": self.captcha_data.get('type', '2'),
            "version": self.captcha_data.get('version', '2.21.5'),
            "dpr": "1",
            "dev": "1",
            "cb": cb,
            "ipv6": "false",
            "runEnv": "10",
            "group": "",
            "scene": "",
            "width": "320",
            "token": "",
            "referer": "",
            "callback": callback
        }
        r = requests.get('https://c.dun.163.com/api/v2/get', params=data, headers=headers, timeout=2)
        data_ = json.loads(re.findall('.*?\((.*?)\);', r.text)[0])
        token = data_['data']['token']
        request.urlretrieve(data_['data']['front'][0], file_path.CAPTCHA_IMG_1_PATH)
        request.urlretrieve(data_['data']['bg'][0], file_path.CAPTCHA_IMG_2_PATH)
        distance = get_gap() + 5
        trace = get_track(distance)
        left = trace[-1][0] - 10
        data_ = crypto_param.get_data(token, trace, left)
        cb = crypto_param.get_cb()

        # 生成actoken
        ctx = get_ctx(file_path.CAPTCHA_ACTOKEN_JS_PATH)
        rdtm = ctx.call('rdtm')
        did = self.get_actoken_median(ctx, rdtm)
        if not actoken:
            actoken = ctx.call('actoken', rdtm, did)

        # 提交验证部分
        get_data = {
            "id": self.captcha_id,
            "token": token,
            "acToken": actoken,
            "data": data_,
            "width": "320",
            "type": self.captcha_data.get('type', '2'),
            "version": self.captcha_data.get('version', '2.21.5'),
            "cb": cb,
            "extraData": "",
            "runEnv": "10",
            "referer": "",
            "callback": "__JSONP_48mk47t_1"
        }
        r = requests.get('https://c.dun.163.com/api/v2/check', headers=headers, params=get_data)
        if self.counter == 1:
            try:
                data = r.text[18:-2]
                self.result = json.loads(data)
                self.secure_captcha = get_secure_captcha(self.result['data']['validate'], self.fp, self.result['data']['zoneId'])
            except:
                pass
        else:
            self.counter += 1
            self.validate(actoken)


