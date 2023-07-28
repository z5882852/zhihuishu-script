import datetime
import logging

from utils.utils import get_log_folder, enable_log_level, enable_log, print_info_level


def setup_logger(logfile, log_level=logging.DEBUG):
    # 创建一个logger
    logger = logging.getLogger('my_logger')
    logger.setLevel(log_level)

    # 创建一个文件handler，用于将日志写入文件
    file_handler = logging.FileHandler(logfile, encoding="utf-8", mode="a")
    file_handler.setLevel(log_level)

    # 创建一个格式化器，定义日志格式
    formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    # 将文件handler添加到logger
    logger.addHandler(file_handler)
    return logger


class Logger:
    def __init__(self):
        # 获取当前日期
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        # 设置日志文件名和等级
        logfile = f"{get_log_folder()}{current_date}.log"
        log_level = logging.DEBUG
        # 创建日志模块
        self.logger = setup_logger(logfile, log_level)
        self.enable_log = enable_log()
        self.enable_level = enable_log_level()
        self.print_info_level = print_info_level()

    def debug(self, message):
        if enable_log and "debug" in self.enable_level:
            self.logger.debug(message)

    def info(self, message):
        if self.print_info_level:
            print(message)
        if enable_log and "info" in self.enable_level:
            self.logger.info(message)

    def warning(self, message):
        if enable_log and "warning" in self.enable_level:
            self.logger.warning(message)

    def error(self, message):
        if enable_log and "error" in self.enable_level:
            self.logger.error(message)

    def critical(self, message):
        if enable_log and "critical" in self.enable_level:
            self.logger.critical(message)