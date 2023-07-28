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

from captcha.captcha import yidun
from utils.encrypt import get_login_captcha_id, get_login_captcha_v
from utils.utils import merge_dict, append_cookies, get_user


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
        response = self.session.get(url, headers=self.headers, params=params)
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
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            return False, f"登录失败, status_code: {response.status_code}"
        data = response.json()
        if data.get("status", 0) == -2:
            return False, f"登录失败, 账号或密码错误"
        elif data.get("status", 0) == 1:
            self.pwd = data.get("pwd", None)
            return True, "登录成功"
        return False, f"登录失败, response: {response.text}"

    def gologin(self, url):
        """获取cookies关键内容"""
        response = self.session.get(url, headers=self.headers, allow_redirects=False)
        if not (response.status_code in (200, 302)):
            return False, response
        return True, response

    def login(self):
        """
        登录，成功则返回cookies
        :return: cookies
        """
        username = self.user.get("username", "username")
        password = self.user.get("password", "password")
        success, msg = self.validate_account_password(username, password)
        if not success:
            return success, msg
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
            if new_url == "https://onlineweb.zhihuishu.com" or "SESSION" in requests.utils.dict_from_cookiejar(self.session.cookies):
                break
            success, response = self.gologin(new_url)
            if not success:
                return False, f"登录失败, {response.status_code}"
        if not self.get_user_info():
            return False, "登录失败, 无法验证身份"
        return True, "登录成功"


    def save_cookies(self):
        """保存cookies至本地"""
        if not self.user_data:
            return False
        if not requests.utils.dict_from_cookiejar(self.session.cookies):
            return False
        if not ("uuid" in self.user_data):
            return False
        append_cookies(get_user().get("username"), requests.utils.dict_from_cookiejar(self.session.cookies))
