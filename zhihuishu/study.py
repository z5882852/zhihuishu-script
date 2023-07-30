import json
from urllib.parse import unquote

import requests

from zhihuishu.course import ShareCourse
from utils.encrypt import EncryptShareVideoSaveParams, get_token_id, gen_watch_point
from utils.utils import get_error_retry


class StudyShareCourse:
    def __init__(self, recruit_and_course_id, session, logger, speed=1.5):
        # 传入参数
        self.recruit_and_course_id = recruit_and_course_id
        self.speed = speed

        # 课程数据，一般不变
        self.recruit_id = None
        self.course_name = None
        self.course_id = None
        self.lessons = []

        # 正在学习的视频课数据
        self.viewing_video_info = None
        self.studied_lesson_dto_id = None
        self.video_name = None
        self.questions = []

        # 其他
        self.session = session
        self.ShareCourse = ShareCourse(session)
        self.logger = logger
        self.uuid = None
        self.finish = False

    def start(self):
        error_num = 0
        while error_num < get_error_retry():
            if self.finish:
                break
            try:
                self.init()
                self.study()
                break
            except Exception as e:
                error_num += 1
                print(f"发生错误: {e}")
                self.logger.warning(e)


    def init(self):
        # 获取用户uuid
        self.get_uuid()
        self.logger.debug(f"uuid: {self.uuid}")
        # 获取cookies
        self.ShareCourse.go_login(f"https://studyh5.zhihuishu.com/videoStudy.html#/studyVideo?recruitAndCourseId={self.recruit_and_course_id}")
        # 查询课程信息
        self.query_course_info()
        self.logger.info("查询课程信息成功!")
        self.logger.debug(f"recruit_id: {self.recruit_id}, course_name: {self.course_name}, course_id: {self.course_id}")
        # 获取视频信息
        self.get_video_list()
        self.logger.info("获取视频列表信息成功!")
        self.logger.debug(f"len(self.lessons): {len(self.lessons)}")
        self.logger.debug(f"self.lessons: {self.lessons}")
        # 查询各个视频学习进度
        self.query_study_info()
        self.logger.info("查询视频学习进度成功!")
        while True:
            print(
                "1. 从头开始学习"
                "\n2. 从上次观看视频开始学习"
            )
            mode = input("请选择学习模式：")
            if mode == "1":
                # 从头开始学习
                self.viewing_video_info = self.lessons[0]
                break
            elif mode == "2":
                # 获取上次观看视频的信息
                self.get_last_view_video_id()
                self.logger.info("获取上次观看视频的信息成功!")
                self.logger.debug(f"self.viewing_video_info: {self.viewing_video_info}")
                break
            else:
                print("输入错误，请重新输入")

    def study(self):
        while not self.finish:
            # 学习该课视频
            self.study_lesson()
            # 切换下一个视频
            self.next_video()
        self.logger.debug(f"课程 {self.course_name} 学习完成")
        print(f"课程 {self.course_name} 学习完成")

    def study_lesson(self):
        # 获取当前视频信息
        self.video_name = f"{self.viewing_video_info.get('chapter_name')}"
        self.video_name += f"-{self.viewing_video_info.get('lesson_name')}"
        if self.viewing_video_info.get("small_lesson_id"):
            self.video_name += f"-{self.viewing_video_info.get('small_lesson_name')}"

        # 判断当前视频是否学习结束
        if self.viewing_video_info.get("watch_state") == 1:
            self.logger.info(f"{self.video_name}学习进度已满")
            return

        # 获取弹题数据
        self.get_questions()
        self.logger.debug(f"获取弹题数据成功, self.questions: {self.questions}")

        # 创建保存时间点
        # 开始时间
        start_time = self.viewing_video_info.get('study_total_time')
        # 结束时间
        end_time = self.viewing_video_info.get('video_sec')
        # 生成保存时间点
        time_points = self.generate_time_point(start_time, end_time, 300)

        point_index = 0
        local_total_time = start_time
        err_num = 1

        print(f"开始学习视频: {self.video_name}")
        while True:
            # time.sleep(1)
            # 检测是否为最后一个保存点
            if point_index >= len(time_points):
                break
            # 初始化
            local_total_time += self.speed
            time_point_info = time_points[point_index]
            time_point = time_point_info.get("time")
            question_id = time_point_info.get("question_id", None)
            # 判断是否达到保存点
            if time_point > local_total_time:
                continue
            try:
                # 判断是否有弹题
                if question_id:
                    self.logger.debug(f"自动提交弹题, question_id: {question_id}")
                    self.pass_questions(questions_id=question_id)
                # 请求获取视频数据
                pre_learning_note_data = self.get_studied_lesson_dto()
                # 判断是否需要推理验证
                if pre_learning_note_data.get("isSlide", False):
                    input("需要安全验证，请在网页或APP中手动验证后按回车继续...")
                # 获取studied_lesson_dto_id用于生成token_id
                self.studied_lesson_dto_id = pre_learning_note_data.get("studiedLessonDto", {}).get("id", None)
                # 该视频已学习的时间
                study_total_time = pre_learning_note_data.get("studiedLessonDto", {}).get("studyTotalTime", None)
                if not self.save_study(time_point, study_total_time):
                    Exception("无法保存学习进度!")
                point_index += 1
            except Exception as e:
                print(f"保存学习进度发生错误: {e}")
                self.logger.warning(f"保存学习进度发生错误: {e}")
                err_num += 1
                if err_num >= get_error_retry():
                    break
        # 验证视频是否学习完成
        if self.query_current_video_study_finish():
            self.logger.debug(f"{self.video_name} 学习完成")
        else:
            self.logger.warning(f"{self.video_name} 学习失败")

    def get_uuid(self):
        cookies = requests.utils.dict_from_cookiejar(self.session.cookies)
        if not ("CASLOGC" in cookies):
            return
        user_info = cookies.get("CASLOGC", None)
        try:
            self.uuid = json.loads(unquote(user_info)).get("uuid", None)
            if not self.uuid:
                self.logger.info("获取UUID失败")
        except Exception as e:
            self.logger.warning(e)

    def query_course_info(self):
        """查询课程信息"""
        data = self.ShareCourse.query_course_info(self.recruit_and_course_id)
        if data.get("studyStatus", "-1") != "0":
            raise Exception("该课程已经学习过或无法学习")
        course_info = data.get("courseInfo")
        self.recruit_id = data.get("recruitId")
        self.course_name = course_info.get("name")
        self.course_id = course_info.get("courseId")

    def get_video_list(self):
        """获取课程所有视频信息并构建成列表"""
        data = self.ShareCourse.get_video_list(self.recruit_and_course_id)
        self.logger.debug(f"response_video_list: {data}")
        video_chapter_dtos = data.get("videoChapterDtos")
        video_order_number = 1
        for video_chapter_dto in video_chapter_dtos:
            chapter_id = video_chapter_dto.get("id")
            chapter_name = video_chapter_dto.get("name")
            video_lessons = video_chapter_dto.get("videoLessons")
            for video_lesson in video_lessons:
                lesson_id = video_lesson.get("id")
                lesson_name = video_lesson.get("name")
                video_small_lessons = video_lesson.get("videoSmallLessons", None)
                if not video_small_lessons:
                    video_id = video_lesson.get("videoId")
                    video_sec = video_lesson.get("videoSec")
                    is_studied_lesson = video_lesson.get("isStudiedLesson")
                    lesson_info = {
                        "video_order_number": video_order_number,
                        "chapter_id": chapter_id,
                        "chapter_name": chapter_name,
                        "lesson_id": lesson_id,
                        "lesson_name": lesson_name,
                        "small_lesson_id": None,
                        "small_lesson_name": None,
                        "video_id": video_id,
                        "video_sec": video_sec,
                        "is_studied_lesson": is_studied_lesson,
                    }
                    self.lessons.append(lesson_info)
                    video_order_number += 1
                    continue
                for video_small_lesson in video_small_lessons:
                    small_lesson_id = video_small_lesson.get("id")
                    small_lesson_name = video_small_lesson.get("name")
                    video_id = video_small_lesson.get("videoId")
                    video_sec = video_small_lesson.get("videoSec")
                    is_studied_lesson = video_small_lesson.get("isStudiedLesson")
                    lesson_info = {
                        "video_order_number": video_order_number,
                        "chapter_id": chapter_id,
                        "chapter_name": chapter_name,
                        "lesson_id": lesson_id,
                        "lesson_name": lesson_name,
                        "small_lesson_id": small_lesson_id,
                        "small_lesson_name": small_lesson_name,
                        "video_id": video_id,
                        "video_sec": video_sec,
                        "is_studied_lesson": is_studied_lesson,
                    }
                    self.lessons.append(lesson_info)
                    video_order_number += 1
        if len(self.lessons) == 0:
            raise Exception("视频列表为空!")

    def query_study_info(self):
        """查询各个视频的学习进度"""
        query_lessons_ids = []
        query_small_lesson_ids = []
        # 获取所有视频id
        for lesson in self.lessons:
            query_lessons_ids.append(lesson.get("lesson_id")) if lesson.get("lesson_id") else None
            query_small_lesson_ids.append(lesson.get("small_lesson_id")) if lesson.get("small_lesson_id") else None
        # 去重
        query_lessons_ids = list(set(query_lessons_ids))
        query_small_lesson_ids = list(set(query_small_lesson_ids))
        # 查询视频学习进度
        data = self.ShareCourse.query_study_info(lessonIds=query_lessons_ids, lessonVideoIds=query_small_lesson_ids, recruitId=self.recruit_id)
        self.logger.debug(f"study_info: {data}")
        # 更新主视频学习进度
        for lesson_id in data.get("lesson"):
            study_total_time = data.get("lesson").get(lesson_id).get("studyTotalTime")
            watch_state = data.get("lesson").get(lesson_id).get("watchState")
            for i in range(len(self.lessons)):
                # 判断是否为主视频
                if self.lessons[i].get("small_lesson_id", None):
                    continue
                if self.lessons[i].get("lesson_id") == int(lesson_id):
                    self.lessons[i]["study_total_time"] = study_total_time
                    self.lessons[i]["watch_state"] = watch_state
        # 更新子视频学习进度
        for lv_id in data.get("lv"):
            study_total_time = data.get("lv").get(lv_id).get("studyTotalTime")
            watch_state = data.get("lv").get(lv_id).get("watchState")
            for i in range(len(self.lessons)):
                if self.lessons[i].get("small_lesson_id") == int(lv_id):
                    self.lessons[i]["study_total_time"] = study_total_time
                    self.lessons[i]["watch_state"] = watch_state

    def get_last_view_video_id(self):
        """获取上次观看视频的信息"""
        data = self.ShareCourse.query_user_recruit_id_last_video_id(self.recruit_id)
        last_view_video_id = data.get("lastViewVideoId")
        last_view_video_info = None
        for lesson in self.lessons:
            if lesson.get("video_id") == last_view_video_id:
                last_view_video_info = lesson
                break
        if not last_view_video_info:
            raise Exception("无法获取上次观看视频的信息")
        self.viewing_video_info = last_view_video_info

    def get_questions(self):
        """获取弹题数据"""
        data = self.ShareCourse.get_video_pointer_info(
            lessonId=self.viewing_video_info.get("lesson_id"),
            recruitId=self.recruit_id,
            courseId=self.course_id,
            small_lesson_id=self.viewing_video_info.get("small_lesson_id")
        )
        self.questions = data.get("questionPoint")

    def get_studied_lesson_dto(self):
        """获取token_id"""
        data = self.ShareCourse.query_pre_learning_note(
            ccCourseId=self.course_id,
            chapterId=self.viewing_video_info.get("chapter_id"),
            lessonId=self.viewing_video_info.get("lesson_id"),
            recruitId=self.recruit_id,
            videoId=self.viewing_video_info.get("video_id"),
            small_lesson_id=self.viewing_video_info.get("small_lesson_id")
        )
        self.logger.debug(f"pre_learning_note: {data}")
        return data

    def save_study(self, save_time, last_time):
        encrypt_params = self.init_encrypt_params_class()
        data = self.ShareCourse.save_database_interval_time_v2(
            ewssw=gen_watch_point(last_time, save_time),
            sdsew=encrypt_params.get_ev(save_time, last_time),
            zwsds=get_token_id(studied_lesson_dto_id=self.studied_lesson_dto_id),
            courseId=self.course_id
        )
        return data.get("submitSuccess", False)

    def query_current_video_study_finish(self):
        """查询当前视频的学习是否完成"""
        small_lesson_id = self.viewing_video_info.get("small_lesson_id", None)
        lesson_id = self.viewing_video_info.get("lesson_id", None)
        if small_lesson_id:
            data = self.ShareCourse.query_study_info(lessonIds=[], lessonVideoIds=[small_lesson_id], recruitId=self.recruit_id)
        else:
            data = self.ShareCourse.query_study_info(lessonIds=[lesson_id], lessonVideoIds=[], recruitId=self.recruit_id)
        self.logger.debug(f"current_study_info: {data}")
        if small_lesson_id:
            result = data.get("lv", {}).get(str(small_lesson_id), {}).get("watchState", 0) == 1
        else:
            result = data.get("lesson", {}).get(str(lesson_id), {}).get("watchState", 0) == 1
        return result

    def generate_time_point(self, start_time, video_end_time, interval_time=300):
        """
        生成保存时间点
        :param start_time: int 视频开始时间
        :param video_end_time: int 视频结束时间
        :param interval_time: int 间隔时间
        :return: list(dict)
        """
        time_points = []
        point_time = start_time
        while True:
            next_point = False
            # 上一个保存点
            last_time = point_time
            # 下一个保存点
            point_time = min(last_time + interval_time, video_end_time)
            # 判断下一个保存点之间是否有弹题，有则下一个保存点为弹题时间点
            questions_list = self.questions
            if questions_list is None:
                questions_list = []
            for question in questions_list:
                question_time = question.get("timeSec")
                if last_time < question_time < point_time:
                    point_time = question_time
                    time_points.append({
                        "time": point_time,
                        "question_id": question.get("questionIds"),
                    })
                    next_point = True
                    continue
            if next_point:
                if point_time == video_end_time:
                    break
                continue
            time_points.append({
                "time": point_time,
                "question_id": None,
            })
            if point_time == video_end_time:
                break
        self.logger.debug(f"保存时间点: {time_points}")
        return time_points

    def init_encrypt_params_class(self):
        """初始化获取保存学习进度的参数类"""
        encrypt = EncryptShareVideoSaveParams(
            recruit_and_course_id=self.recruit_and_course_id,
            recruit_id=self.recruit_id,
            lesson_ld=self.viewing_video_info.get("lesson_id"),
            small_lesson_id=self.viewing_video_info.get("small_lesson_id"),
            video_id=self.viewing_video_info.get("video_id"),
            chapter_id=self.viewing_video_info.get("chapter_id"),
            video_sec=self.viewing_video_info.get("video_sec"),
            uuid=self.uuid
        )
        return encrypt

    def pass_questions(self, questions_id):
        """
        自动提交问题
        :param questions_id: 问题id
        """
        # 获取问题数据
        question_data = self.ShareCourse.get_popup_exam(
            lessonId=self.viewing_video_info.get("lesson_id"),
            questionIds=questions_id,
            small_lesson_id=self.viewing_video_info.get("small_lesson_id")
        )
        if not question_data.get("lessonTestQuestionUseInterfaceDtos", []):
            Exception("题目信息为空")
        # 查询答案
        answer_list = []
        question_data = question_data.get("lessonTestQuestionUseInterfaceDtos", [])[0].get("testQuestion", {})
        self.logger.debug(f"question_data: {question_data}")
        for option in question_data.get("questionOptions", {}):
            if option.get("result", "-1") == "1":
                answer_list.append(str(option.get("id", "0")))
        answer = ",".join(answer_list)
        self.logger.debug(f"answer: {answer}")
        # 提交答案
        result = self.ShareCourse.submit_popup_exam(
            courseId=self.course_id,
            recruitId=self.recruit_id,
            testQuestionId=questions_id,
            lessonId=self.viewing_video_info.get("lesson_id"),
            answer=answer,
            isCurrent="1",
            small_lesson_id=self.viewing_video_info.get("small_lesson_id"),
        )
        # 查询提交结果
        self.logger.debug(f"submit_question_result: {result}")
        success = result.get("submitStatus", False)
        return success

    def next_video(self):
        """切换下一个视频"""
        next_video_info = None
        next_video_order_number = self.viewing_video_info.get("video_order_number") + 1
        if len(self.lessons) == next_video_order_number:
            self.finish = True
            return False
        for lesson in self.lessons:
            if lesson.get("video_order_number") == next_video_order_number:
                next_video_info = lesson
                break
        if not next_video_info:
            raise Exception("无法切换下一个视频：下一个视频为空")
        self.viewing_video_info = next_video_info