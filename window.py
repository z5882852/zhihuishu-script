import ctypes
import os

import requests
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

from PyQt5.QtCore import QThreadPool
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QLineEdit

from utils.config import is_save_cookies, get_settings_config, get_data_config, get_config
from utils.logger import Logger
from utils.path import ICON_PATH
from utils.utils import get_cookies, save_cookies, read_description
from components.main_ui import Ui_MainGUI
from zhihuishu.auth import UserHandler


class MainGUI(QtWidgets.QWidget, Ui_MainGUI):
    def __init__(self, logger_instance):
        super(MainGUI, self).__init__()
        self.setupUi(self)
        # 设置窗口标题
        self.setWindowTitle("智慧树刷课脚本")
        # 设置窗口图标
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))
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

        # 初始化
        self.threadpool = QThreadPool()
        self.logger = logger_instance
        self.isLogining = False
        self.isLogin = False
        self.session = None
        self.UserAuth = None
        self.init()


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
        if not self.UserAuth.get_user_info():
            # 无法验证用户，停留登录界面
            self.logger.info("无法验证用户")
            # 清除cookies
            self.session.cookies = requests.utils.cookiejar_from_dict({})
            return None
        # 验证身份成功
        self.username_label.setText(self.UserAuth.user_data.get("realName", "未知用户名"))
        self.logger.info("验证身份成功")
        self.logger.debug("user_info: %s" % self.UserAuth.user_data)
        self.isLogin = True
        self.show_create_task_page()

    def show_login_page(self):
        if self.stackedWidget_content.currentIndex() == 0:
            return None
        self.stackedWidget_content.setCurrentIndex(0)
        self.stackedWidget_login.setCurrentIndex(0)

    def show_create_task_page(self):
        if self.stackedWidget_content.currentIndex() == 1:
            return None
        self.stackedWidget_content.setCurrentIndex(1)
        # QInputDialog.getText(self, "输入", "请输入课程ID", QLineEdit.Normal, "默认值")

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
            QMessageBox.information(self, "提示", "请输入用户名和密码", QMessageBox.Ok)
            self.isLogining = False
            self.login_Button.setDisabled(False)
            return None
        success, mes = self.UserAuth.login(username, password)
        self.isLogining = False
        if not success:
            QMessageBox.information(self, "提示", mes, QMessageBox.Ok)
            self.login_Button.setDisabled(False)
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
        course_type = self.courseType_comboBox.currentText()
        course_name = self.courseName_comboBox.currentText()
        study_mode = self.studyMode_comboBox.currentIndex()
        play_speed = self.speed_doubleSpinBox.value()
        max_study_time = self.maxStudyTime_spinBox.value()
        max_study_video_num = self.maxStudyVideoNum_spinBox.value()
        violent_mode = self.violent_checkBox.isChecked()
        print_log = self.printLog_checkBox.isChecked()
        setting = (course_type, course_name, study_mode, play_speed, max_study_time, max_study_video_num, violent_mode, print_log)
        self.logger.debug(f"task_setting: \n{setting}")
        if None in setting:
            QMessageBox.warning(self, "提示", "任务设置不完整，请查看日志", QMessageBox.Ok)
            return None
        if course_name == "":
            QMessageBox.warning(self, "提示", "请选择课程", QMessageBox.Ok)
            return None
        task_setting = {
            "course_type": course_type,
            "course_name": course_name,
            "study_mode": study_mode,
            "play_speed": play_speed,
            "max_study_time": max_study_time,
            "max_study_video_num": max_study_video_num,
            "violent_mode": violent_mode,
            "print_log": print_log
        }
        print(task_setting)

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



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
    logger = Logger()
    logger.info("################脚本开始运行################")
    ui = MainGUI(logger)
    ui.show()
    sys.exit(app.exec_())