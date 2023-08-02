import base64
import json
import time

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from captcha.space_inference import SpaceInference
from utils.config import get_config

# 2.js 登录   key: 7q9oko0vqb3la20r
# 4.js 视频   key: azp53h0kft7qi78q
# ?.js 问答   key: kcGOlISPkYKRksSK
# ?.js 考试   key: onbfhdyvz8x7otrp

'''
# 获取主要加密参数
'''


def get_login_captcha_id():
    return get_config().get('encrypt', 'login_captcha_id')


def get_login_captcha_v():
    return get_config().get('encrypt', 'login_captcha_v')


def get_space_inference_captcha_id():
    return get_config().get('encrypt', 'space_inference_captcha_id')


def get_space_inference_captcha_v():
    return get_config().get('encrypt', 'space_inference_captcha_v')


def get_AES_keys(key_name):
    return get_config().get('encrypt', key_name)


def get_ev_key(key_name):
    return get_config().get('encrypt', key_name)


'''
加密部分
'''


def AES_CBC_encrypt(key, iv, text):
    """AES的CBC模式加密字符串"""
    # 将AES_KEY和vi转换为字节类型
    key = key.encode('utf-8')
    iv = iv.encode('utf-8')
    # 初始化AES加密器
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # 使用PKCS7填充
    padded_plaintext = pad(text.encode('utf-8'), AES.block_size)
    # 加密数据
    ciphertext = cipher.encrypt(padded_plaintext)
    # 对加密结果进行base64编码
    encrypted_data = base64.b64encode(ciphertext).decode('utf-8')
    return encrypted_data


def encrypt_params(params, key_name):
    if isinstance(params, dict):
        params = json.dumps(params, separators=(',', ':'))
    return AES_CBC_encrypt(key=get_AES_keys(key_name), iv=get_config().get('encrypt', 'AES_IV'), text=params)


def get_token_id(studied_lesson_dto_id):
    return base64.b64encode(str(studied_lesson_dto_id).encode()).decode()


def encrypt_ev(data: list, key: str):
    """
    获取ev参数
    :param data: 构建ev参数的列表
    :param key: 密钥
    :return: str
    """

    def gen():
        while True:
            for char in key:
                yield ord(char)

    gen = gen()
    data = ';'.join(map(str, data))
    ev = ""
    for c in data:
        tmp = hex(ord(c) ^ next(gen)).replace("0x", "")
        if len(tmp) < 2:
            tmp = '0' + tmp
        ev += tmp[-4:]  # actually -2 is fine, but their sauce code said -4
    return ev


def gen_watch_point(start_time, end_time):
    """
    生成watchPoint（提交共享学分课视频进度接口用）
    :param start_time: 起始视频进度条时间，秒
    :param end_time: 提交时间
    """
    record_interval = 1990
    total_study_time_interval = 4990
    cache_interval = 180000
    database_interval = 300000
    watch_point = None
    total_stydy_time = start_time
    i_time = end_time - start_time
    for i in range(1, int(i_time * 1000) + 1):
        if i % total_study_time_interval == 0:
            total_stydy_time += 5
        if i % record_interval == 0 and i >= record_interval:
            t = int(total_stydy_time / 5) + 2
            if watch_point is None:
                watch_point = '0,1,'
            else:
                watch_point += ','
            watch_point += str(t)
    return watch_point


class EncryptShareVideoSaveParams:
    def __init__(self, recruit_and_course_id, recruit_id, lesson_ld, small_lesson_id, video_id, chapter_id, video_sec,
                 uuid):
        """
        构建共享学分课视频查看进度的加密参数类
        """
        self.recruit_and_course_id = recruit_and_course_id
        self.recruit_id = recruit_id
        self.lesson_ld = lesson_ld
        self.small_lesson_id = small_lesson_id
        self.video_id = video_id
        self.chapter_id = chapter_id
        self.video_sec = video_sec
        self.uuid = uuid

    def set_ev_list(self, played_time: int, last_submit_time: int):
        """
        构建ev参数列表
        """
        # 判断small_lesson_id是否为存在
        if self.small_lesson_id is None:
            self.small_lesson_id = 0
        ev = [
            self.recruit_id,
            self.lesson_ld,
            self.small_lesson_id,
            self.video_id,
            self.chapter_id,
            '0',
            int(played_time - last_submit_time),
            int(played_time),
            self.format_video_sec(played_time),
            self.uuid + "zhs"
        ]
        return ev

    def get_ev(self, played_time: int, last_submit_time: int, ev_key_name='D26666_KEY'):
        """
        获取ev参数
        :param played_time: int 当前保存的时间点
        :param last_submit_time: int 上次保存的时间
        :param ev_key_name: 密钥名
        :return: str
        """
        return encrypt_ev(self.set_ev_list(played_time, last_submit_time), get_ev_key(ev_key_name))

    @staticmethod
    def format_video_sec(sec: int):
        """
        格式化视频秒数
        将视频秒数转换为例如"00:00:00"的格式
        :return: str
        """
        h = sec // 3600
        m = sec % 3600 // 60
        s = sec % 60
        return f"{h:02}:{m:02}:{s:02}"


class Validate:
    def __init__(self, session=None, logger=None, recruit_id=None, lesson_id=None, small_lesson_id=None, last_view_video_id=None, chapterId=None):
        """通过安全验证码"""
        self.session = session
        self.logger = logger
        self.ev_list = [
            recruit_id,
            lesson_id,
            small_lesson_id if small_lesson_id is not None else 0,
            last_view_video_id,
            chapterId
        ]
        self.logger.debug(f"构建的ev参数列表为：{self.ev_list}")

    def get_encrypted_params(self, secure_captcha):
        """获取加密后的参数"""
        params = {
            "token": secure_captcha,
            "ev": encrypt_ev(self.ev_list, get_ev_key('D26666_KEY')),
            "checkType": 1
        }
        self.logger.debug(f"构建的参数为：{params}")
        params = encrypt_params(params, 'study_aes_key')
        return params

    def validate_slide_token(self, secure_captcha):
        headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://studyvideoh5.zhihuishu.com",
            "Pragma": "no-cache",
            "Referer": "https://studyvideoh5.zhihuishu.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188",
            "sec-ch-ua": "\"Not/A)Brand\";v=\"99\", \"Microsoft Edge\";v=\"115\", \"Chromium\";v=\"115\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\""
        }
        url = "https://studyservice-api.zhihuishu.com/gateway/t/v1/learning/validateSlideToken"
        data = {
            "secretStr": self.get_encrypted_params(secure_captcha),
            "dateFormate": int(time.time() * 1000)
        }
        response = self.session.post(url, headers=headers, data=data)
        self.logger.debug(f"验证验证码的状态码： {response.status_code}, 响应：{response.text}")
        if response.status_code != 200:
            return False
        data = response.json().get('data', {})
        return data.get('status', '0') == "200" and data.get('pass', False)
