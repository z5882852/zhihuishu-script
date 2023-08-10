"""
智慧树用户认证模块
用法:
   # >>> cookies = "your cookies"
   # >>> UH = UserHandler(cookies=cookies)  # 初始化
   # >>> login_success = UH.get_user_info()  # 尝试获取用户数据
   # >>> print(UH.user_data)  # 返回用户数据
"""

import base64
import json
import time
import urllib

import requests
import websockets

from captcha.captcha import yidun
from utils.encrypt import get_login_captcha_id, get_login_captcha_v
from utils.utils import append_cookies, get_user


def get_validate():
    """
    获取validate
    :return: secure_captcha validate
    """
    # 初始化验证id
    yd = yidun(get_login_captcha_id())
    # 设置参数
    yd.captcha_data['v'] = get_login_captcha_v()
    # 获取加密的验证码
    yd.validate()
    return yd.secure_captcha


def get_secret_str(username, password):
    """
    根据用户名、密码计算secretStr(登录参数)
    :param username: 用户名
    :param password: 密码
    :return: secretStr
    """
    # 获取validate
    validate = get_validate()
    # 检查validate是否为None
    if validate is None:
        return None
    params = json.dumps({
        'account': username,
        'password': password,
        'validate': validate,
    }, separators=(',', ':'))
    text = urllib.parse.quote(params)
    # 不转换冒号和逗号
    text = text.replace("%3A", ":").replace("%2C", ",")
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')


class UserHandler:
    def __init__(self, session):
        self.user = get_user()
        self.session = session
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://passport.zhihuishu.com",
            "Pragma": "no-cache",
            "Referer": "https://passport.zhihuishu.com/login?service=https://onlineservice-api.zhihuishu.com/gateway/f/v1/login/gologin",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": "\"Not/A)Brand\";v=\"99\", \"Microsoft Edge\";v=\"115\", \"Chromium\";v=\"115\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\""
        }
        self.pwd = None
        self.user_data = None

    def get_user_info(self):
        """获取用户数据，保存至self.user_data，获取失败则返回False"""
        url = "https://onlineservice-api.zhihuishu.com/gateway/f/v1/login/getLoginUserInfo"
        params = {
            "time": int(time.time())
        }
        response = self.session.get(url, headers=self.headers, params=params, timeout=3)
        if response.status_code != 200:
            return False
        data = response.json()
        if data.get("code", 500) == 200:
            self.user_data = data.get("result", None)
            return True
        return False

    def validate_account_password(self, username, password):
        """
        验证用户名和密码是否正确，返回登录令牌pwd
        :param username: 用户名
        :param password: 密码
        :return: 是否成功, 消息
        """
        secret_str = get_secret_str(username, password)
        if not secret_str:
            return False, "获取验证码失败"
        url = "https://passport.zhihuishu.com/user/validateAccountAndPassword"
        data = {"secretStr": secret_str}
        response = self.session.post(url, headers=self.headers, data=data, timeout=3)
        if response.status_code != 200:
            return False, f"登录失败, status_code: {response.status_code}"
        data = response.json()
        if data.get("status", 0) == 1:
            self.pwd = data.get("pwd", None)
            return True, "登录成功"
        elif data.get("status", 0) == -2:
            return False, "登录失败, 账号或密码错误"
        elif data.get("status", 0) == -4:
            return False, "登录失败, 验证码错误"
        elif data.get("status", 0) == -5:
            return False, "应网络安全要求，您的密码安全级别太低，为了保障您的账户安全，请立即修改密码"
        elif data.get("status", 0) == -6:
            return False, "登录失败, 连续登陆5次错误, 禁止5分钟"
        elif data.get("status", 0) == -8:
            return False, "登录失败, 需要教师验证, 请用手机号登录"
        elif data.get("status", 0) == -9:
            return False, "登录失败, 账户存在异常活动, 请前往网页验证手机号"
        elif data.get("status", 0) == -10:
            return False, "你已被禁止登录, 由于你未通过验证, 今日24:00点以前将无法登录智慧树"
        elif data.get("status", 0) == -11:
            return False, "登录失败, 服务异常, 请稍后再试"
        elif data.get("status", 0) == -12:
            return False, "登录失败, 发现有异常学习行为, 请前往网页解除"
        elif data.get("status", 0) == -13:
            return False, "登录失败, 需要空间推理验证"
        return False, f"登录失败, response: {response.text}"

    def abnormal_login_code_validate(self, validate_code):
        url = "https://passport.zhihuishu.com/user/abnormalLoginCodeValidate"
        data = {
            "code": validate_code
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            return False, f"验证失败, status_code: {response.status_code}"
        try:
            data = response.json()
        except Exception as e:
            return False, f"验证失败, response: {response.text}"
        if data.get("status", 0) == 1:
            self.pwd = data.get("pwd", None)
            return self.pwd_login()
        elif data.get("status", 0) == 2:
            return False, "你已被禁止登录, 由于你未通过验证, 今日24:00点以前将无法登录智慧树"
        elif data.get("status", 0) == 3:
            return False, "短信验证码错误"
        elif data.get("status", 0) == 4:
            return False, "滑块验证码错误"
        return False, f"验证失败, response: {response.text}"

    def gologin(self, url):
        """获取cookies关键内容"""
        response = self.session.get(url, headers=self.headers, allow_redirects=False)
        if not (response.status_code in (200, 302)):
            return False, response
        return True, response

    def login(self, username=None, password=None):
        """
        账号密码登录
        :param username: 用户名
        :param password: 密码
        :return: 是否成功, 消息
        """
        if username is None or password is None:
            username = self.user.get("username", "username")
            password = self.user.get("password", "password")
        success, msg = self.validate_account_password(username, password)
        if not success:
            return success, msg
        return self.pwd_login()

    def pwd_login(self):
        if not self.pwd:
            return False, "无法获取pwd"
        url = "https://passport.zhihuishu.com/login"
        params = {
            "pwd": self.pwd,
            "service": "https://onlineservice-api.zhihuishu.com/gateway/f/v1/login/gologin"
        }
        response = self.session.get(url, headers=self.headers, params=params, allow_redirects=False)
        if response.status_code != 302:
            return False, f"登录失败, status_code: {response.status_code}"
        while True:
            new_url = response.headers.get("location", None)
            if new_url is None:
                return False, "登录失败: new_url is None"
            if new_url == "https://onlineweb.zhihuishu.com" or "SESSION" in requests.utils.dict_from_cookiejar(
                    self.session.cookies):
                break
            success, response = self.gologin(new_url)
            if not success:
                return False, f"登录失败, {response.status_code}"
        if not self.get_user_info():
            return False, "登录失败, 无法验证身份"
        return True, "登录成功"

    def get_qr_code(self):
        """
        获取二维码
        :return: dict
        """
        qr_page = "https://passport.zhihuishu.com/qrCodeLogin/getLoginQrImg"
        response = self.session.get(qr_page, timeout=5)
        if response.status_code != 200:
            return None
        data = response.json()
        qrToken = data.get("qrToken", None)
        img = data.get("img", None)
        return {
            "qr_token": qrToken,
            "img": img
        }

    async def validate_qr_code(self, qr_token, callback=None, callback_info=None, logger=None):
        """
        验证二维码
        :param qr_token: 令牌
        :param callback: 回调函数
        :param callback_info: 消息回调函数
        :param logger: 日志记录器
        :return: message
        """
        params = {
            "qrToken": qr_token
        }
        url = f"wss://appcomm-user.zhihuishu.com/app-commserv-user/websocket?{urllib.parse.urlencode(params)}"
        async with websockets.connect(url, extra_headers=self.session.headers) as websocket:
            while True:
                data = json.loads(await websocket.recv())
                msg = data.get("msg", "Unknown Message")
                code = data.get("code", -1)
                if code == 0:
                    if logger:
                        logger.info(msg)
                    callback_info(msg)
                elif code == 1:
                    if logger:
                        logger.info(msg)
                    callback_info(msg)
                    self.pwd = data.get("oncePassword", None)
                    success, msg = self.pwd_login()
                    callback(success, msg)
                    return None
                elif code == 2:
                    if logger:
                        logger.warning(msg)
                    callback(False, msg)
                    return None
                else:
                    if logger:
                        logger.warning(msg)
                    callback(False, msg)
                    return None

    def save_cookies(self):
        """保存cookies至本地"""
        if not self.user_data:
            return False
        if not requests.utils.dict_from_cookiejar(self.session.cookies):
            return False
        if not ("uuid" in self.user_data):
            return False
        append_cookies(get_user().get("username"), requests.utils.dict_from_cookiejar(self.session.cookies))
