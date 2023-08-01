import requests

from utils.config import is_save_cookies
from zhihuishu.auth import UserHandler
from zhihuishu.course import QueryCourse
from zhihuishu.study import TerminalStudyShareCourse
from utils.logger import Logger
from utils.utils import get_cookies, save_cookies


def run(speed=1):
    # 初始化日志模块
    logger = Logger()
    logger.info("################脚本开始运行################")
    # 初始化session
    session = requests.Session()
    if is_save_cookies():
        session.cookies = get_cookies()
    # 初始化用户模块
    UH = UserHandler(session)
    # 验证用户状态
    if not UH.get_user_info():
        # 无法验证用户，尝试重新登录
        logger.info("正在登录")
        # 清除cookies
        session.cookies = requests.utils.cookiejar_from_dict({})
        # 登录
        success, mes = UH.login()
        logger.info(mes)
        if not success:
            logger.info("登录失败")
            exit(0)
    logger.info("验证身份成功")

    # 脚本主循环
    while True:
        # 查询共享学分课程
        QC = QueryCourse(session=session, logger=logger)
        share_sourses = QC.query_share_sourse()
        print("请选择要学习的课程：")
        index = 1
        # 打印课程列表
        for share_sourse in share_sourses:
            name = share_sourse.get("courseName")
            progress = share_sourse.get("progress")
            print(f"{index}. {name} {progress}")
            index += 1
        try:
            input_str = input("请输入序号(输入`quit`退出)：")
            if input_str in ("quit", "exit", "退出"):
                break
            index = int(input_str)
            if index > len(share_sourses) or index < 1:
                # 输入错误
                raise ValueError

            # 开始学习
            secret = share_sourses[index - 1].get("secret")
            SSC = TerminalStudyShareCourse(recruit_and_course_id=secret, session=session, logger=logger, speed=speed)
            SSC.start()

        except ValueError:
            print("输入错误，请重新输入")
        except KeyboardInterrupt:
            print("已停止")
            break

    if is_save_cookies():
        # 保存cookies
        save_cookies(session)
        logger.debug("保存cookies成功")
    # 关闭session
    session.close()

    logger.info("################脚本运行结束################")


if __name__ == "__main__":
    run()