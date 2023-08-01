import os
import sys

ROOT_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
RES_PATH = os.path.join(ROOT_PATH, "components", "res")
IMAGE_PATH = os.path.join(RES_PATH, "images")
ICON_PATH = os.path.join(IMAGE_PATH, "icon.png")
USER_IMG_PATH = os.path.join(IMAGE_PATH, "user.jpg")
CONFIG_PATH = os.path.join(ROOT_PATH, "config.ini")
CONFIG_TEMPLATE_PATH = os.path.join(RES_PATH, "template", "config.ini.template")
