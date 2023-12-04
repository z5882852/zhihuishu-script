import os
import sys

ROOT_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
RES_PATH = os.path.join(ROOT_PATH, "components", "res")
IMAGE_PATH = os.path.join(RES_PATH, "images")
ICON_PATH = os.path.join(IMAGE_PATH, "icon.png")
USER_IMG_PATH = os.path.join(IMAGE_PATH, "user.jpg")
CONFIG_PATH = os.path.join(ROOT_PATH, "config.ini")
CONFIG_TEMPLATE_PATH = os.path.join(RES_PATH, "template", "config.ini.template")
NODEJS_PATH = os.path.join(RES_PATH, "node.exe")

# Linux系统请在这里设置NodeJs路径
# NODEJS_PATH = os.path.join(os.path.dirname("/usr/local/bin/"), "node")

CAPTCHA_PATH = os.path.join(ROOT_PATH, "captcha")

CAPTCHA_ACTOKEN_JS_PATH = os.path.join(CAPTCHA_PATH, "js", "actoken.js")
CAPTCHA_CB_JS_PATH = os.path.join(CAPTCHA_PATH, "js", "cb.js")
CAPTCHA_FP_JS_PATH = os.path.join(CAPTCHA_PATH, "js", "fp.js")
CAPTCHA_SC_JS_PATH = os.path.join(CAPTCHA_PATH, "js", "secureCaptcha.js")


CAPTCHA_IMG_1_PATH = os.path.join(CAPTCHA_PATH, "img", "1.png")
CAPTCHA_IMG_2_PATH = os.path.join(CAPTCHA_PATH, "img", "2.jpg")
CAPTCHA_IMG_3_PATH = os.path.join(CAPTCHA_PATH, "img", "3.png")
