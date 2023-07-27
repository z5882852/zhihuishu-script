import configparser
import json
import os



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
        write_json_file({}, cookies_path)
    cookies = read_json_file(cookies_path)
    return cookies.get(username, {})


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


def get_user():
    return {
        "username": get_config().get('user', 'username'),
        "password": get_config().get('user', 'password'),
    }


def get_cookies_path():
    return get_config().get('data', 'cookies_path')


def get_cookies():
    return read_cookies(get_user().get("username"))


def set_cookies(cookies):
    append_cookies(get_user().get("username"), cookies)


