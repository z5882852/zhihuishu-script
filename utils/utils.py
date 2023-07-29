import configparser
import json
import os

from requests.cookies import RequestsCookieJar, create_cookie


def merge_dict(dict_1: dict, dict_2: dict):
    dict_3 = {}
    dict_3.update(dict_1)
    dict_3.update(dict_2)
    return dict_3


def is_file_exists(file_path):
    return os.path.exists(file_path)


def create_folder(folder_path):
    # 查询文件夹是否存在。
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        json_data = json.load(file)
    return json_data


def write_json_file(json_data, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(json_data, file, ensure_ascii=False)


def read_cookies(username):
    cookies_path = get_cookies_path()
    if not is_file_exists(cookies_path):
        write_json_file([], cookies_path)
    cookies = read_json_file(cookies_path)
    return list_to_cookie_jar(cookies.get(username, []))


def append_cookies(username, cookies):
    cookies_path = get_cookies_path()
    if not is_file_exists(cookies_path):
        write_json_file({}, cookies_path)
    new_cookies = read_json_file(cookies_path)
    new_cookies[username] = cookies
    write_json_file(new_cookies, cookies_path)


def get_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    return config


def save_cookies(session):
    # cookies = requests.utils.cookie_jar_to_list(session.cookies)
    cookies = cookie_jar_to_list(session.cookies)
    if not cookies:
        return
    append_cookies(get_user().get("username"), cookies)


def cookie_jar_to_list(cookie_jar: RequestsCookieJar):
    cookies = []
    for cookie in cookie_jar:
        cookie_dict = {
            'name': cookie.name,
            'value': cookie.value,
            'domain': cookie.domain,
            'port': cookie.port,
            'path': cookie.path,
            'expires': cookie.expires,
            'secure': cookie.secure,
            'rest': cookie.__dict__.get('_rest', {}),
            'version': cookie.version,
            'comment': cookie.comment,
            'comment_url': cookie.comment_url,
            'rfc2109': cookie.rfc2109,
            'discard': cookie.discard,
        }
        cookies.append(cookie_dict)
    return cookies


def list_to_cookie_jar(cookies_list: list[dict]):
    cookie_jar = RequestsCookieJar()
    for cookie_dict in cookies_list:
        cookie = create_cookie(
            name=cookie_dict['name'],
            value=cookie_dict['value'],
            domain=cookie_dict.get('domain', ''),
            port=cookie_dict.get('port', None),
            path=cookie_dict.get('path', '/'),
            expires=cookie_dict.get('expires', None),
            secure=cookie_dict.get('secure', False),
            rest=cookie_dict.get('rest', {'HttpOnly': None}),
            version=cookie_dict.get('version', 0),
            comment=cookie_dict.get('comment', None),
            comment_url=cookie_dict.get('comment_url', None),
            rfc2109=cookie_dict.get('rfc2109', False),
            discard=cookie_dict.get('discard', True),
        )
        cookie_jar.set_cookie(cookie)
    return cookie_jar


def get_user():
    return {
        "username": get_config().get('user', 'username'),
        "password": get_config().get('user', 'password'),
    }


def is_save_cookies():
    return get_config().get('settings', 'save_cookies')


def get_log_folder():
    return get_config().get('data', 'log_folder')


def get_cookies_path():
    return get_config().get('data', 'cookies_path')


def get_cookies():
    return read_cookies(get_user().get("username"))


def set_cookies(cookies):
    append_cookies(get_user().get("username"), cookies)


def get_error_retry():
    return int(get_config().get('settings', 'error_retry'))


def enable_log():
    return get_config().get('settings', 'enable_log') == "true"


def enable_log_level():
    return get_config().get('settings', 'enable_log_level').split(",")


def print_info_level():
    return get_config().get('settings', 'print_info_level') == "true"


