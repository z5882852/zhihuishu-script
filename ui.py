import asyncio
import base64
import ctypes

import requests
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

from PyQt5.QtCore import QThreadPool, pyqtSignal, QThread
from PyQt5.QtWidgets import QMessageBox, QDesktopWidget

from captcha.space_inference import SpaceInference
from components.captcha_ui import Ui_CaptchaGUI
from utils.config import is_save_cookies, get_settings_config, get_config, get_user
from utils.encrypt import get_space_inference_captcha_id, get_space_inference_captcha_v
from utils.logger import Logger
from utils.path import ICON_PATH, USER_IMG_PATH
from utils.utils import get_cookies, save_cookies, read_description, download_image
from components.main_ui import Ui_MainGUI
from zhihuishu.auth import UserHandler
from zhihuishu.course import QueryCourse
from zhihuishu.study import StudyShareCourse


class MainGUI(QtWidgets.QWidget, Ui_MainGUI):
    def __init__(self, logger_instance, captcha_instance=None):
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
        self.ClearLog_Button.clicked.connect(self.clear_run_log)
        self.StopStudy_Button.clicked.connect(self.stop_study)
        # 绑定暴力模式选中事件
        self.violent_checkBox.stateChanged.connect(self.toggle_speed)
        # 绑定courseType_comboBox的选中事件
        self.courseType_comboBox.currentIndexChanged.connect(self.courseType_comboBox_currentIndexChanged)
        # 绑定courseName_comboBox的选中事件
        self.courseName_comboBox.currentIndexChanged.connect(self.courseName_comboBox_currentIndexChanged)

        self.select_RAC_id = None  # 选中的课程id
        self.share_course_list = []  # 共享课程列表
        self.micro_course_list = []  # 校内学分课列表

        # 初始化线程
        self.thread = None
        self.refresh_thread = None
        self.study_thread = None

        # 初始化
        self.threadpool = QThreadPool()
        self.logger = logger_instance
        self.login_captcha = None
        self.captcha = None
        self.isLogining = False
        self.isLogin = False
        self.session = None
        self.UserAuth = None
        self.init()

    def init(self):
        """初始化"""
        # 设置默认用户
        self.set_default_user()
        # 初始化session
        self.session = requests.Session()
        if is_save_cookies():
            self.session.cookies = get_cookies()
        # 初始化用户模块
        self.UserAuth = UserHandler(self.session)
        # 验证用户身份
        self.validate_user()

    def set_default_user(self):
        """设置默认用户"""
        # 设置用户名
        self.username_label.setText("未登录")
        # 设置头像
        image = QtGui.QPixmap(USER_IMG_PATH).scaled(260, 260)
        self.userImg_label.setPixmap(image)
        self.userImg_label.setScaledContents(True)

    def validate_user(self):
        """验证用户身份"""
        # 验证用户状态
        try:
            if not self.UserAuth.get_user_info():
                # 无法验证用户，停留登录界面
                self.logger.info("无法验证用户")
                # 清除cookies
                self.session.cookies = requests.utils.cookiejar_from_dict({})
                # 将配置的用户名和密码设置到输入框
                user = get_user()
                self.Username_Input.setText(user.get("username", ""))
                self.Password_Input.setText(user.get("password", ""))
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
        self.logger.debug("user_info: %s" % self.UserAuth.user_data)
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
        # 将图片显示在标签上
        image = QtGui.QPixmap()
        image.loadFromData(img_data)
        scaled_image = image.scaled(260, 260, aspectRatioMode=QtCore.Qt.KeepAspectRatio)
        # 切割图片为圆形
        scaled_image = get_circular_pixmap(scaled_image, 260)
        self.userImg_label.setPixmap(scaled_image)
        self.userImg_label.setScaledContents(True)

    def show_login_page(self):
        """显示登录页面"""
        if self.stackedWidget_content.currentIndex() == 0:
            return None
        self.stackedWidget_content.setCurrentIndex(0)
        self.stackedWidget_login.setCurrentIndex(0)

    def show_create_task_page(self):
        """显示任务创建页面"""
        if self.stackedWidget_content.currentIndex() == 1:
            return None
        self.stackedWidget_content.setCurrentIndex(1)
        index = self.courseType_comboBox.currentIndex()
        self.courseType_comboBox_currentIndexChanged(index)

    def show_progress_page(self):
        """显示任务进度页面"""
        if self.stackedWidget_content.currentIndex() == 2:
            return None
        self.stackedWidget_content.setCurrentIndex(2)

    def show_setting_page(self):
        """显示设置页面"""
        if self.stackedWidget_content.currentIndex() == 3:
            return None
        self.stackedWidget_content.setCurrentIndex(3)
        self.load_settings()

    def show_qrcode_page(self):
        """显示二维码页面"""
        if self.stackedWidget_login.currentIndex() == 1:
            return None
        if self.isLogin:
            reply = QMessageBox.question(self, '提示', '该操作会退出账号，是否继续？', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return None
        self.stackedWidget_login.setCurrentIndex(1)
        self.refresh_qrcode()

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
        # 防止重复点击
        if self.isLogining:
            return None
        self.isLogining = True
        # 禁用登录按钮
        self.login_Button.setDisabled(True)
        username = self.Username_Input.text()
        password = self.Password_Input.text()
        if not username or not password:
            self.isLogining = False
            self.login_Button.setDisabled(False)
            QMessageBox.information(self, "提示", "请输入用户名和密码", QMessageBox.Ok)
            return None
        try:
            success, mes = self.UserAuth.login(username, password)
        except Exception as e:
            self.isLogining = False
            self.login_Button.setDisabled(False)
            self.logger.error("登录失败，错误信息: %s" % e)
            QMessageBox.information(self, "提示", "登录失败，错误信息: %s" % e, QMessageBox.Ok)
            return None
        if mes == "登录失败, 需要空间推理验证":
            # 打开验证窗口
            self.open_login_captcha_window()
            return None
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
            self.logger.info("cookies已保存")
            self.logger.debug("cookies: \n%s" % get_cookies())
        self.isLogin = True
        self.login_Button.setDisabled(False)
        self.show_user_info()
        QMessageBox.information(self, "提示", mes, QMessageBox.Ok)
        self.show_create_task_page()

    def open_login_captcha_window(self):
        # 打开验证码窗口
        def login_verify_success(token):
            success, mes = self.UserAuth.abnormal_login_code_validate(token)
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
                self.logger.info("cookies已保存")
                self.logger.debug("cookies: \n%s" % get_cookies())
            self.isLogin = True
            self.login_Button.setDisabled(False)
            self.show_user_info()
            QMessageBox.information(self, "提示", mes, QMessageBox.Ok)
            self.show_create_task_page()

        def login_verify_fail():
            self.isLogining = False
            self.login_Button.setDisabled(False)
            if self.isLogin:
                return None
            QMessageBox.information(self, "提示", "登录失败", QMessageBox.Ok)

        self.login_captcha = LoginCaptchaGUI(
            session=self.session,
            logger_instance=self.logger,
        )
        # 设置新窗口在顶层
        self.login_captcha.setWindowFlags(self.login_captcha.windowFlags())
        self.login_captcha.load_captcha()
        self.login_captcha.show()
        # 绑定信号
        self.login_captcha.verify_success.connect(login_verify_success)
        self.login_captcha.verify_fail.connect(login_verify_fail)

    def refresh_qrcode(self):
        def handle_info_message(success, message):
            self.isLogin = success
            QMessageBox.information(self, "提示", message, QMessageBox.Ok)

        def handle_qr_code_image(data):
            image = QtGui.QPixmap()
            image.loadFromData(data)
            scaled_image = image.scaled(100, 100, aspectRatioMode=QtCore.Qt.KeepAspectRatio)
            self.qrcode_img_label.setPixmap(scaled_image)
            self.qrcode_img_label.setScaledContents(True)

        def handle_qr_code_info(message):
            self.QRCodeInfo_label.setText(message)

        # 清除cookies
        self.session.cookies = requests.utils.cookiejar_from_dict({})
        # 设置默认用户
        self.set_default_user()
        # 清空二维码
        self.qrcode_img_label.clear()
        # 设置二维码信息
        self.QRCodeInfo_label.setText("请扫描二维码登录")
        # 开启线程
        self.refresh_thread = RefreshQRCodeThread(self.UserAuth, logger=self.logger, isLogin=self.isLogin)
        self.refresh_thread.info_message.connect(handle_info_message)
        self.refresh_thread.qr_code_image.connect(handle_qr_code_image)
        self.refresh_thread.finished.connect(self.handle_qr_code_validation)
        self.refresh_thread.show_info.connect(handle_qr_code_info)

        self.refresh_thread.start()

    def handle_qr_code_validation(self, is_login):
        """处理二维码验证"""
        if not is_login:
            return None
        if is_save_cookies():
            # 保存cookies
            save_cookies(self.session)
            self.logger.info("cookies已保存")
            self.logger.debug("cookies: \n%s" % get_cookies())
        self.show_create_task_page()
        self.show_user_info()

    def reset_task_page(self):
        """重置任务页面"""
        self.courseType_comboBox.setCurrentIndex(0)
        self.courseName_comboBox.setCurrentIndex(0)
        self.studyMode_comboBox.setCurrentIndex(0)
        self.speed_doubleSpinBox.setValue(1.0)
        self.maxStudyTime_spinBox.setValue(0)
        self.maxStudyVideoNum_spinBox.setValue(0)
        self.violent_checkBox.setChecked(False)
        self.printLog_checkBox.setChecked(True)

    def open_captcha_window(self, v):
        # 打开验证码窗口
        self.captcha = CaptchaGUI(
            session=self.session,
            logger_instance=self.logger,
            Validate_instance=v
        )
        self.captcha.load_captcha()
        self.captcha.show()
        # 绑定信号
        self.captcha.verify_success.connect(self.verify_success)
        self.captcha.verify_fail.connect(self.verify_fail)

    def verify_success(self):
        self.study_thread.SSC.set_verify_success()
        self.captcha.close()

    def verify_fail(self):
        self.study_thread.SSC.set_verify_failed()
        self.captcha.close()

    def create_task(self):
        """创建任务"""
        if self.isLogin is False:
            QMessageBox.warning(self, "提示", "请先登录", QMessageBox.Ok)
            return None
        course_type = self.courseType_comboBox.currentIndex()
        course_name_index = self.courseName_comboBox.currentIndex()
        study_mode = self.studyMode_comboBox.currentIndex()
        play_speed = self.speed_doubleSpinBox.value()
        max_study_time = self.maxStudyTime_spinBox.value()
        max_study_video_num = self.maxStudyVideoNum_spinBox.value()
        violent_mode = self.violent_checkBox.isChecked()
        print_log = self.printLog_checkBox.isChecked()
        setting = (
            course_type,
            self.select_RAC_id,
            study_mode,
            play_speed,
            max_study_time,
            max_study_video_num,
            violent_mode,
            print_log
        )
        if self.select_RAC_id is None:
            QMessageBox.warning(self, "提示", "请选择课程", QMessageBox.Ok)
            return None
        if None in setting:
            self.logger.warning("任务设置不完整, setting: %s" % str(setting))
            QMessageBox.warning(self, "提示", "任务设置不完整，请查看日志", QMessageBox.Ok)
            return None
        task_setting = {
            "course_type": course_type,
            "select_RAC_id": self.select_RAC_id,
            "study_mode": study_mode,
            "play_speed": play_speed,
            "max_study_time": max_study_time,
            "max_study_video_num": max_study_video_num,
            "violent_mode": violent_mode,
            "print_log": print_log
        }
        self.logger.debug(f"task_setting: \n{task_setting}")
        self.show_progress_page()
        self.study(task_setting)

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
                # if len(self.share_course_list) > 0:
                #     self.courseName_comboBox_currentIndexChanged(0)
            elif index == 1:
                # 校内学分课
                self.courseName_comboBox.clear()
                micro_courses = QC.query_micro_course()
                self.micro_course_list = parse_courses(micro_courses)
                self.courseName_comboBox.addItems(get_course_names(self.micro_course_list))
                # if len(self.share_course_list) > 0:
                #     self.courseName_comboBox_currentIndexChanged(0)
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
        self.logger.debug(f"secret course data: {course}")
        self.select_RAC_id = course.get("secret", None)

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

    def study(self, settings):
        """开始学习"""
        if self.study_thread is not None:
            QMessageBox.warning(self, "提示", "正在学习中，请勿重复点击", QMessageBox.Ok)
            return None
        # 初始化
        self.studing_label.setText("")
        self.clear_run_log()
        self.course_progressBar.setValue(0)
        self.video_progressBar.setValue(0)

        def handle_studing_info(message):
            self.logger.debug(message)
            self.studing_label.setText(message)

        def handle_set_course_progress(progress):
            self.logger.debug(f"course_progress: {progress}")
            self.course_progressBar.setValue(int(progress))

        def handle_set_video_progress(progress):
            self.logger.debug(f"video_progress: {progress}")
            self.video_progressBar.setValue(int(progress))

        def handle_study_finished(success):
            self.logger.debug("学习结束")
            self.study_log.append("学习结束\n")
            self.stop_study()

        # 创建线程
        self.study_thread = StudyThread(
            RAC_id=self.select_RAC_id,
            session=self.session,
            logger=self.logger,
            settings=settings
        )
        # 绑定信号
        self.study_thread.studing_info.connect(handle_studing_info)
        self.study_thread.show_study_info.connect(self.handle_study_info)
        self.study_thread.set_course_progress.connect(handle_set_course_progress)
        self.study_thread.set_video_progress.connect(handle_set_video_progress)
        self.study_thread.security_check.connect(self.open_captcha_window)
        self.study_thread.finished.connect(handle_study_finished)

        self.study_thread.start()

    def stop_study(self):
        """停止学习"""
        if self.study_thread is None:
            return None
        self.logger.debug("停止学习")
        self.study_thread.SSC.stop()
        self.study_thread.quit()
        self.study_thread.wait()
        self.study_thread.SSC = None
        self.study_thread = None

    def handle_study_info(self, message):
        self.study_log.append(message)

    def clear_run_log(self):
        """清空日志"""
        self.study_log.clear()

    def closeEvent(self, event):
        """关闭窗口事件"""
        reply = QMessageBox.question(self, '提示', '确认退出？', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


class LoginCaptchaGUI(QtWidgets.QWidget, Ui_CaptchaGUI):
    # 绑定信号
    verify_success = QtCore.pyqtSignal(str)
    verify_fail = QtCore.pyqtSignal()

    def __init__(self, session=None, logger_instance=None):
        super(LoginCaptchaGUI, self).__init__()
        self.setupUi(self)
        self.setGeometry(0, 0, 400, 300)
        self.center()
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        # 绑定按钮事件
        self.verify_Button.clicked.connect(self.verify)
        # 禁用按钮
        self.verify_Button.setEnabled(False)

        # 初始化
        self.session = session
        self.logger = logger_instance

        self.SI = SpaceInference(get_space_inference_captcha_id())
        self.SI.captcha_data['type'] = '11'
        self.SI.captcha_data['v'] = get_space_inference_captcha_v()
        self.position = {'x': 0.00, 'y': 0.00}
        self.captcha_data = None


    def load_captcha(self):
        """加载验证码"""
        self.verify_Button.setEnabled(False)
        # 获取验证码数据
        self.captcha_data = self.SI.get_captcha()
        captcha_image_urls = self.captcha_data.get('data', {}).get('bg', None)
        if captcha_image_urls is None:
            return
        self.logger.debug("captcha_img_url: %s" % captcha_image_urls[0])
        try:
            img_data = download_image(self.session, captcha_image_urls[0])
        except Exception as e:
            # 弹窗警告窗口
            QMessageBox.warning(self, "警告", "无法获取验证图片，错误信息: %s" % e, QMessageBox.Yes)
            self.logger.error("无法获取验证图片，错误信息: %s" % e)
            return None
        if img_data is None:
            self.logger.warning("无法获取验证图片")
            return None
        # 将图片显示在标签上
        image = QtGui.QPixmap()
        image.loadFromData(img_data)
        scaled_image = image.scaled(320, 160, aspectRatioMode=QtCore.Qt.KeepAspectRatio)
        self.captcha_img.setPixmap(scaled_image)
        self.captcha_img.setScaledContents(True)
        # 设置提示
        prompt = self.captcha_data.get('data', {}).get('front', None)
        self.logger.debug("captcha_prompt: %s" % prompt)
        if prompt is None:
            return
        self.captcha_prompt.setText(prompt)

    def verify(self):
        """验证"""
        self.verify_Button.setEnabled(False)
        x = self.position['x']
        y = self.position['y']
        self.SI.check(x, y)
        self.logger.debug("验证结果: %s" % self.SI.result)
        token = self.SI.secure_captcha
        if token is None:
            # 弹窗警告窗口
            QMessageBox.warning(self, "警告", "验证失败，请重试", QMessageBox.Yes)
            # 重新加载验证码
            self.load_captcha()
            return
        self.logger.debug("token: %s" % token)
        # 验证成功，返回token
        self.verify_success.emit(token)
        self.close()

    def closeEvent(self, event):
        """关闭窗口事件"""
        self.verify_fail.emit()
        event.accept()

    def mousePressEvent(self, event):
        # 获取鼠标点击事件的位置
        pos = event.pos()
        # 判断点击是否在标签上
        if self.captcha_img.geometry().contains(pos):
            # 保留两位小数
            x = float('%.2f' % ((pos.x() - 40) / 320))
            y = float('%.2f' % ((pos.y() - 10) / 160))

            self.position['x'] = x
            self.position['y'] = y
            self.position_x.setText(str(self.position['x']))
            self.position_y.setText(str(self.position['y']))
            self.logger.debug('点击了标签，位置： %s, %s' % (x, y))
            # 启用按钮
            self.verify_Button.setEnabled(True)

    def center(self):
        """居中显示"""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            int((screen.width() - size.width()) / 2),
            int((screen.height() - size.height()) / 2)
        )


class CaptchaGUI(QtWidgets.QWidget, Ui_CaptchaGUI):
    # 绑定信号
    verify_success = QtCore.pyqtSignal()
    verify_fail = QtCore.pyqtSignal()

    def __init__(self, session=None, logger_instance=None, Validate_instance=None):
        super(CaptchaGUI, self).__init__()
        self.setupUi(self)
        self.setGeometry(0, 0, 400, 300)
        self.center()
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        # 绑定按钮事件
        self.verify_Button.clicked.connect(self.verify)
        # 禁用按钮
        self.verify_Button.setEnabled(False)

        # 初始化
        self.session = session
        self.logger = logger_instance
        self.validate = Validate_instance
        self.SI = SpaceInference(get_space_inference_captcha_id())
        self.SI.captcha_data['type'] = '11'
        self.SI.captcha_data['v'] = get_space_inference_captcha_v()
        self.position = {'x': 0.00, 'y': 0.00}
        self.captcha_data = None
        self.token = None
        # self.load_captcha()


    def load_captcha(self):
        """加载验证码"""
        self.verify_Button.setEnabled(False)
        # 获取验证码数据
        self.captcha_data = self.SI.get_captcha()
        captcha_image_urls = self.captcha_data.get('data', {}).get('bg', None)
        if captcha_image_urls is None:
            return
        self.logger.debug("captcha_img_url: %s" % captcha_image_urls[0])
        try:
            img_data = download_image(self.session, captcha_image_urls[0])
        except Exception as e:
            # 弹窗警告窗口
            QMessageBox.warning(self, "警告", "无法获取验证图片，错误信息: %s" % e, QMessageBox.Yes)
            self.logger.error("无法获取验证图片，错误信息: %s" % e)
            return None
        if img_data is None:
            self.logger.warning("无法获取验证图片")
            return None
        # 将图片显示在标签上
        image = QtGui.QPixmap()
        image.loadFromData(img_data)
        scaled_image = image.scaled(320, 160, aspectRatioMode=QtCore.Qt.KeepAspectRatio)
        self.captcha_img.setPixmap(scaled_image)
        self.captcha_img.setScaledContents(True)
        # 设置提示
        prompt = self.captcha_data.get('data', {}).get('front', None)
        self.logger.debug("captcha_prompt: %s" % prompt)
        if prompt is None:
            return
        self.captcha_prompt.setText(prompt)

    def verify(self):
        """验证"""
        self.verify_Button.setEnabled(False)
        x = self.position['x']
        y = self.position['y']
        self.SI.check(x, y)
        self.logger.debug("验证结果: %s" % self.SI.result)
        token = self.SI.secure_captcha
        if token is None:
            # 弹窗警告窗口
            QMessageBox.warning(self, "警告", "验证失败，请重试", QMessageBox.Yes)
            # 重新加载验证码
            self.load_captcha()
            return
        self.token = token
        self.logger.debug("token: %s" % token)
        # 验证
        success = self.validate.validate_slide_token(token)
        if success:
            self.verify_success.emit()
        else:
            # 弹窗警告窗口
            QMessageBox.warning(self, "警告", "未知错误，请在网页或APP验证", QMessageBox.Yes)
            self.verify_fail.emit()

    def closeEvent(self, event):
        """关闭窗口事件"""
        self.verify_fail.emit()
        event.accept()

    def mousePressEvent(self, event):
        # 获取鼠标点击事件的位置
        pos = event.pos()
        # 判断点击是否在标签上
        if self.captcha_img.geometry().contains(pos):
            # 保留两位小数
            x = float('%.2f' % ((pos.x() - 40) / 320))
            y = float('%.2f' % ((pos.y() - 10) / 160))

            self.position['x'] = x
            self.position['y'] = y
            self.position_x.setText(str(self.position['x']))
            self.position_y.setText(str(self.position['y']))
            self.logger.debug('点击了标签，位置： %s, %s' % (x, y))
            # 启用按钮
            self.verify_Button.setEnabled(True)

    def center(self):
        """居中显示"""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            int((screen.width() - size.width()) / 2),
            int((screen.height() - size.height()) / 2)
        )


class RefreshQRCodeThread(QThread):
    finished = pyqtSignal(bool)
    info_message = pyqtSignal(bool, str)
    qr_code_image = pyqtSignal(bytes)
    show_info = pyqtSignal(str)

    def __init__(self, UserAuth, logger=None, isLogin=False):
        super(RefreshQRCodeThread, self).__init__()
        self.UserAuth = UserAuth
        self.logger = logger
        self.isLogin = isLogin

    def print_info(self, success, message):
        self.isLogin = success
        self.info_message.emit(success, message)

    def print_message(self, data):
        self.logger.info(data)
        self.show_info.emit(data)

    def show_qrcode_img(self, img):
        img = base64.b64decode(img)
        self.qr_code_image.emit(img)

    def run(self):
        qr_data = self.UserAuth.get_qr_code()
        qr_token = qr_data["qr_token"]
        self.show_qrcode_img(qr_data.get("img", None))
        asyncio.run(
            self.UserAuth.validate_qr_code(
                qr_token,
                logger=self.logger,
                callback=self.print_info,
                callback_info=self.print_message
            )
        )
        if not self.isLogin:
            self.finished.emit(False)
        else:
            self.finished.emit(True)


class StudyThread(QThread):
    studing_info = pyqtSignal(str)
    show_study_info = pyqtSignal(str)
    set_course_progress = pyqtSignal(float)
    set_video_progress = pyqtSignal(float)
    # 安全验证
    security_check = pyqtSignal(object)
    finished = pyqtSignal(bool)

    def __init__(self, RAC_id=None, session=None, logger=None, settings=None):
        super(StudyThread, self).__init__()
        self.SSC = None
        self.RAC_id = RAC_id
        self.session = session
        self.logger = logger
        self.settings = settings

    def studing_info_callback(self, message):
        self.studing_info.emit(message)

    def show_study_info_callback(self, message):
        self.show_study_info.emit(message)

    def set_course_progress_callback(self, progress):
        self.set_course_progress.emit(progress)

    def set_video_progress_callback(self, progress):
        self.set_video_progress.emit(progress)

    def security_check_callback(self, data):
        self.security_check.emit(data)
        # self.SSC.verify_success = True

    def run(self):
        self.SSC = StudyShareCourse(
            recruit_and_course_id=self.RAC_id,
            session=self.session,
            logger=self.logger,
            settings=self.settings,
            studing_info_callback=self.studing_info_callback,
            show_study_info_callback=self.show_study_info_callback,
            set_course_progress_callback=self.set_course_progress_callback,
            set_video_progress_callback=self.set_video_progress_callback,
            security_check_callback=self.security_check_callback
        )
        self.SSC.start()
        self.finished.emit(True)


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


def run():
    app = QtWidgets.QApplication(sys.argv)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
    logger = Logger()
    logger.info("################脚本开始运行################")
    ui = MainGUI(logger)
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()