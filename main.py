import requests

from auth import UserHandler
from study import StudyShareCourse
from utils.logger import Logger
from utils.utils import get_cookies, save_cookies

session = requests.Session()
logger = Logger()
session.cookies = requests.utils.cookiejar_from_dict(get_cookies())
UH = UserHandler(session)
if not UH.get_user_info():
    logger.info("正在登录")
    session.cookies = requests.utils.cookiejar_from_dict({})
    UHL = UserHandler(session)
    success, mes = UHL.login()
    logger.info(mes)
    if not success:
        logger.info("登录失败")
        exit()
logger.info("验证身份成功")

SSC = StudyShareCourse(recruit_and_course_id="4b505d5847594859454a58595f475e475f", session=session)
SSC.start()

save_cookies(session)