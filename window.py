import ctypes
import os

import requests
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

from PyQt5.QtCore import QThreadPool
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QLineEdit

from utils.config import is_save_cookies, get_settings_config, get_data_config, get_config
from utils.logger import Logger
from utils.path import ICON_PATH, USER_IMG_PATH
from utils.utils import get_cookies, save_cookies, read_description, download_image
from components.main_ui import Ui_MainGUI
from zhihuishu.auth import UserHandler
from zhihuishu.course import QueryCourse


class MainGUI(QtWidgets.QWidget, Ui_MainGUI):
    def __init__(self, logger_instance):
        super(MainGUI, self).__init__()
        self.setupUi(self)
        # 设置窗口标题
        self.setWindowTitle("智慧树刷课脚本")
        # 设置窗口图标
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))
        # 设置用户头像
        image = QtGui.QPixmap(USER_IMG_PATH).scaled(260, 260)
        self.userImg_label.setPixmap(image)
        self.userImg_label.setScaledContents(True)
        # 绑定按钮事件
        self.QRCodePage_Button.clicked.connect(self.show_qrcode_page)
        self.PasswordPage_Button.clicked.connect(self.show_password_page)
        self.refreshQRCode_Button.clicked.connect(self.refresh_qrcode)
        self.login_Button.clicked.connect(self.password_login)
        self.LoginPage_Button.clicked.connect(self.show_login_page)
        self.TaskPage_Button.clicked.connect(self.show_create_task_page)
        self.ProgressPage_Button.clicked.connect(self.show_progress_page)
        self.SettingPage_Button.clicked.connect(self.show_setting_page)
        self.ResetTask_Button.clicked.connect(self.reset_task_page)
        self.CreateTask_Button.clicked.connect(self.create_task)
        self.ResetSetting_Button.clicked.connect(self.reset_setting)
        self.SaveSetting_Button.clicked.connect(self.save_setting)
        # 绑定暴力模式选中事件
        self.violent_checkBox.stateChanged.connect(self.toggle_speed)
        # 绑定courseType_comboBox的选中事件
        self.courseType_comboBox.currentIndexChanged.connect(self.courseType_comboBox_currentIndexChanged)
        # 绑定courseName_comboBox的选中事件
        self.courseName_comboBox.currentIndexChanged.connect(self.courseName_comboBox_currentIndexChanged)

        # 初始化
        self.threadpool = QThreadPool()
        self.logger = logger_instance
        self.isLogining = False
        self.isLogin = False
        self.session = None
        self.UserAuth = None
        self.init()

        self.select_RAC_id = None
        self.share_course_list = []  # 共享课程列表
        self.micro_course_list = []  # 校内学分课列表

    def init(self):
        """初始化"""
        # 初始化session
        self.session = requests.Session()
        if is_save_cookies():
            self.session.cookies = get_cookies()
        # 初始化用户模块
        self.UserAuth = UserHandler(self.session)
        # 验证用户身份
        self.validate_user()

    def validate_user(self):
        """验证用户身份"""
        # 验证用户状态
        try:
            if not self.UserAuth.get_user_info():
                # 无法验证用户，停留登录界面
                self.logger.info("无法验证用户")
                # 清除cookies
                self.session.cookies = requests.utils.cookiejar_from_dict({})
                return None
        except Exception as e:
            self.logger.error("无法验证用户，错误信息: %s" % e)
            return None
        # 验证身份成功
        self.show_user_info()
        self.logger.info("验证身份成功")
        self.logger.debug("user_info: %s" % self.UserAuth.user_data)
        self.isLogin = True
        self.show_create_task_page()

    def show_user_info(self):
        """显示用户信息"""
        self.username_label.setText(self.UserAuth.user_data.get("realName", "未知用户名"))
        img_url = self.UserAuth.user_data.get("headPicUrl", "")
        try:
            img_data = download_image(self.session, img_url)
        except Exception as e:
            self.logger.error("无法获取用户头像，错误信息: %s" % e)
            return None
        if img_data is None:
            self.logger.debug("img_url: %s" % img_url)
            self.logger.warning("无法获取用户头像，使用默认头像")
            return None
        image = QtGui.QPixmap()
        image.loadFromData(img_data)
        scaled_image = image.scaled(260, 260, aspectRatioMode=QtCore.Qt.KeepAspectRatio)
        # 切割图片为圆形
        scaled_image = get_circular_pixmap(scaled_image, 260)
        self.userImg_label.setPixmap(scaled_image)
        self.userImg_label.setScaledContents(True)

    def show_login_page(self):
        if self.stackedWidget_content.currentIndex() == 0:
            return None
        self.stackedWidget_content.setCurrentIndex(0)
        self.stackedWidget_login.setCurrentIndex(0)

    def show_create_task_page(self):
        if self.stackedWidget_content.currentIndex() == 1:
            return None
        self.stackedWidget_content.setCurrentIndex(1)
        index = self.courseType_comboBox.currentIndex()
        self.courseType_comboBox_currentIndexChanged(index)

    def show_progress_page(self):
        if self.stackedWidget_content.currentIndex() == 2:
            return None
        self.stackedWidget_content.setCurrentIndex(2)

    def show_setting_page(self):
        if self.stackedWidget_content.currentIndex() == 3:
            return None
        self.stackedWidget_content.setCurrentIndex(3)
        self.load_settings()

    def show_qrcode_page(self):
        if self.stackedWidget_login.currentIndex() == 1:
            return None
        self.stackedWidget_login.setCurrentIndex(1)

    def show_password_page(self):
        if self.stackedWidget_login.currentIndex() == 0:
            return None
        self.stackedWidget_login.setCurrentIndex(0)

    def load_settings(self):
        """加载配置"""
        _translate = QtCore.QCoreApplication.translate
        setting = get_settings_config()
        settings_description = read_description().get("settings")
        self.setting_table.setRowCount(len(setting))
        for i in range(len(setting)):
            key, value = setting[i]
            description = settings_description.get(key, "无")

            item = QtWidgets.QTableWidgetItem()
            self.setting_table.setVerticalHeaderItem(i, item)
            item = self.setting_table.verticalHeaderItem(i)
            if item is not None:
                item.setText(_translate("MainGUI", str(i + 1)))

            item = QtWidgets.QTableWidgetItem()
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setting_table.setItem(i, 0, item)
            item = self.setting_table.item(i, 0)
            if item is not None:
                item.setText(_translate("MainGUI", key))

            item = QtWidgets.QTableWidgetItem()
            self.setting_table.setItem(i, 1, item)
            item = self.setting_table.item(i, 1)
            if item is not None:
                item.setText(_translate("MainGUI", value))

            item = QtWidgets.QTableWidgetItem()
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setting_table.setItem(i, 2, item)
            item = self.setting_table.item(i, 2)
            if item is not None:
                item.setText(_translate("MainGUI", description))

    def password_login(self):
        """密码登录"""
        if self.isLogining:
            return None
        self.isLogining = True
        self.login_Button.setDisabled(True)
        username = self.Username_Input.text()
        password = self.Password_Input.text()
        if not username or not password:
            self.isLogining = False
            self.login_Button.setDisabled(False)
            QMessageBox.information(self, "提示", "请输入用户名和密码", QMessageBox.Ok)
            return None
        success, mes = self.UserAuth.login(username, password)
        self.isLogining = False
        if not success:
            self.login_Button.setDisabled(False)
            QMessageBox.information(self, "提示", mes, QMessageBox.Ok)
            return None
        # 登录成功
        self.logger.info(mes)
        if is_save_cookies():
            # 保存cookies
            save_cookies(self.session)
            self.logger.debug("cookies已保存")
            self.logger.debug("cookies: \n%s" % get_cookies())
        self.isLogin = True
        self.login_Button.setDisabled(False)
        self.show_user_info()
        QMessageBox.information(self, "提示", mes, QMessageBox.Ok)
        self.show_create_task_page()

    def refresh_qrcode(self):
        pass

    def reset_task_page(self):
        pass

    def create_task(self):
        """创建任务"""
        if self.isLogin is False:
            QMessageBox.warning(self, "提示", "请先登录", QMessageBox.Ok)
            return None
        course_type = self.courseType_comboBox.currentIndex()
        select_RAC_id = self.select_RAC_id
        study_mode = self.studyMode_comboBox.currentIndex()
        play_speed = self.speed_doubleSpinBox.value()
        max_study_time = self.maxStudyTime_spinBox.value()
        max_study_video_num = self.maxStudyVideoNum_spinBox.value()
        violent_mode = self.violent_checkBox.isChecked()
        print_log = self.printLog_checkBox.isChecked()
        setting = (
            course_type,
            select_RAC_id,
            study_mode,
            play_speed,
            max_study_time,
            max_study_video_num,
            violent_mode,
            print_log
        )
        self.logger.debug(f"task_setting: \n{setting}")
        if None in setting:
            QMessageBox.warning(self, "提示", "任务设置不完整，请查看日志", QMessageBox.Ok)
            return None
        if select_RAC_id is None:
            QMessageBox.warning(self, "提示", "请选择课程", QMessageBox.Ok)
            return None
        task_setting = {
            "course_type": course_type,
            "select_RAC_id": select_RAC_id,
            "study_mode": study_mode,
            "play_speed": play_speed,
            "max_study_time": max_study_time,
            "max_study_video_num": max_study_video_num,
            "violent_mode": violent_mode,
            "print_log": print_log
        }
        print(task_setting)

    def courseType_comboBox_currentIndexChanged(self, index):
        """课程类型下拉框选中事件"""
        def parse_courses(courses):
            course_list = []
            for course in courses:
                course_name = course.get("courseName")
                secret_id = course.get("secret")
                progress = course.get("progress")
                course_list.append({
                    "courseName": course_name,
                    "secret": secret_id,
                    "progress": progress
                })
            return course_list

        def get_course_names(course_list):
            course_names = []
            for course in course_list:
                course_name = f"{course.get('courseName')}-{course.get('progress')}"
                course_names.append(course_name)
            return course_names

        if self.isLogin is False:
            return None
        QC = QueryCourse(session=self.session, logger=self.logger)
        try:
            if index == 0:
                # 共享课程
                self.courseName_comboBox.clear()
                share_sourses = QC.query_share_sourse()
                self.share_course_list = parse_courses(share_sourses)
                self.courseName_comboBox.addItems(get_course_names(self.share_course_list))
            elif index == 1:
                # 校内学分课
                self.courseName_comboBox.clear()
                micro_courses = QC.query_micro_course()
                self.micro_course_list = parse_courses(micro_courses)
                self.courseName_comboBox.addItems(get_course_names(self.micro_course_list))
        except Exception as e:
            self.logger.error("获取课程列表失败，错误信息: %s" % e)
            return None

    def courseName_comboBox_currentIndexChanged(self, index):
        """课程选中事件"""
        if self.courseType_comboBox.currentIndex() == 0:
            # 共享课程
            course_list = self.share_course_list
        elif self.courseType_comboBox.currentIndex() == 1:
            # 校内学分课
            course_list = self.micro_course_list
        else:
            return None
        if index < 0 or index >= len(course_list):
            return None
        course = course_list[index]
        course_name = course.get("courseName")
        secret_id = course.get("secret")
        self.logger.debug(f"select course_name: {course_name}")
        self.logger.debug(f"secret_id: {secret_id}")
        self.select_RAC_id = secret_id
        self.logger.debug(f"select_RAC_id: {self.select_RAC_id}")


    def get_share_course_list(self):
        """获取共享课程列表"""
        pass

    def get_micro_course_list(self):
        """获取校内学分课列表"""
        pass

    def toggle_speed(self):
        """选中暴力模式时，速度设置不可用"""
        if self.violent_checkBox.isChecked():
            self.speed_doubleSpinBox.setEnabled(False)
        else:
            self.speed_doubleSpinBox.setEnabled(True)

    def reset_setting(self):
        """重置设置"""
        self.logger.debug("重置设置")
        self.load_settings()

    def save_setting(self):
        """保存设置"""
        # 获取setting_table的所有行
        items = self.setting_table.findItems("", QtCore.Qt.MatchContains)
        # 将行转换为字典
        settings = {}
        for item in items:
            row = item.row()
            key = self.setting_table.item(row, 0).text()
            value = self.setting_table.item(row, 1).text()
            settings[key] = value
        self.logger.debug(f"setting: \n{settings}")
        # 遍历setting
        config = get_config()
        for key, value in settings.items():
            print(key, value)
            config.set(section="settings", option=key, value=value)
        # 保存配置文件
        config.write(open("config.ini", "w"))
        QMessageBox.information(self, "提示", "设置已保存，部分设置重启生效", QMessageBox.Ok)


def get_circular_pixmap(pixmap, size):
    """
    返回一个圆形版本的QPixmap对象
    :param pixmap: 原始QPixmap对象
    :param size: 圆形图片的尺寸（宽度和高度相等）
    :return: 圆形QPixmap对象
    """
    if not pixmap.isNull():
        # 创建一个带有透明背景的临时QPixmap
        circular_pixmap = QtGui.QPixmap(size, size)
        circular_pixmap.fill(QtCore.Qt.transparent)

        # 在临时Pixmap上绘制圆形
        painter = QtGui.QPainter(circular_pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        path = QtGui.QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)

        # 缩放图片以适应圆形区域
        scaled_pixmap = pixmap.scaled(size, size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        # 计算居中绘制的位置
        x = (size - scaled_pixmap.width()) // 2
        y = (size - scaled_pixmap.height()) // 2

        # 绘制缩放后的图片
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()

        return circular_pixmap
    else:
        return QtGui.QPixmap()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
    logger = Logger()
    logger.info("################脚本开始运行################")
    ui = MainGUI(logger)
    ui.show()
    sys.exit(app.exec_())
