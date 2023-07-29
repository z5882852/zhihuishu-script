import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from utils.utils import get_config

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

    def y(_t):
        e_2 = str(hex(_t))[2:]
        if len(e_2) < 2:
            return '0' + e_2
        else:
            return e_2

    e = ''
    for j in data:
        e += str(j) + ';'
    e = e[0:len(e) - 1]
    e_1 = ''
    for i in range(len(e)):
        n = ord(e[i]) ^ ord(key[i % len(key)])
        e_1 += y(n)
    return e_1


class EncryptShareVideoSaveParams:
    def __init__(self, recruit_and_course_id, recruit_id, lesson_ld, small_lesson_id, video_id, chapte_id, video_sec):
        """
        构建共享学分课视频查看进度的加密参数类
        """
        self.recruit_and_course_id = recruit_and_course_id
        self.recruit_id = recruit_id
        self.lesson_ld = lesson_ld
        self.small_lesson_id = small_lesson_id
        self.video_id = video_id
        self.chapte_id = chapte_id
        self.video_sec = video_sec

    def format_video_sec(self):
        """
        格式化视频秒数
        将视频秒数转换为例如"00:00:00"的格式
        :return: str
        """
        h = self.video_sec // 3600
        m = self.video_sec % 3600 // 60
        s = self.video_sec % 60
        return f"{h:02}:{m:02}:{s:02}"

    def set_ev_list(self, played_time: int, last_submit_time: int):
        return [
            self.recruit_id,
            self.lesson_ld,
            self.small_lesson_id,
            self.video_id,
            self.chapte_id,
            '0',
            int(played_time - last_submit_time),
            played_time,
            self.format_video_sec(),
        ]

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
    def gen_watch_point(start_time, end_time=300):
        """
        生成watch_point
        :param start_time: 起始视频进度条时间，秒
        :param end_time: 提交时距离起始时间的间隔，秒。默认为正常观看时请求database接口的间隔时间
        """
        record_interval = 1990
        total_study_time_interval = 4990
        # cache_interval = 180000
        # database_interval = 300000
        watch_point = None
        total_stydy_time = start_time
        for i in range(int(end_time * 1000)):
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


