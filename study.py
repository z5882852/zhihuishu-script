from course import ShareCourse
from utils.logger import Logger
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

        # 其他
        self.session = session
        self.ShareCourse = ShareCourse(session)
        self.logger = logger
        self.finish = False
        self.finish_message = None

    def start(self):
        error_num = 0
        while error_num < get_error_retry():
            if self.finish:
                break
            try:
                self.run()
                break
            except Exception as e:
                error_num += 1
                print(e)
                self.logger.warning(e)
                self.finish_message = "错误"


    def run(self):
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
        self.logger.debug(f"self.lessons: \n{self.lessons}")
        # 查询各个视频学习进度
        self.query_study_info()
        self.logger.info("查询视频学习进度成功!")
        # 获取上次观看视频的信息
        self.get_last_view_video_id()
        self.logger.info("获取上次观看视频的信息成功!")
        self.logger.debug(f"self.viewing_video_info: \n{self.viewing_video_info}")




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
        video_chapter_dtos = data.get("videoChapterDtos")
        video_order_number = 1
        for video_chapter_dto in video_chapter_dtos:
            chapter_id = video_chapter_dto.get("id")
            chapter_name = video_chapter_dto.get("name")
            video_lessons = video_chapter_dto.get("videoLessons")
            for video_lesson in video_lessons:
                lesson_id = video_lesson.get("id")
                lesson_name = video_lesson.get("name")
                video_small_lessons = video_lesson.get("videoSmallLessons")
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
        for lesson in self.lessons:
            query_lessons_ids.append(lesson.get("lesson_id"))
            query_small_lesson_ids.append(lesson.get("small_lesson_id"))
        query_lessons_ids = list(set(query_lessons_ids))
        data = self.ShareCourse.query_study_info(lessonIds=query_lessons_ids, lessonVideoIds=query_small_lesson_ids, recruitId=self.recruit_id)
        self.logger.debug(f"study_info: \n{data}")
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

    def query_current_video_study_finish(self):
        """查询当前视频的学习是否完成"""
        small_lesson_id = self.viewing_video_info.get("small_lesson_id")
        data = self.ShareCourse.query_study_info(lessonIds=[], lessonVideoIds=[small_lesson_id], recruitId=self.recruit_id)
        self.logger.debug(f"current_study_info: \n{data}")
        return data.get("lv").get(int(small_lesson_id)).get("watchState") == 1

    def next_video(self):
        """切换下一个视频"""
        next_video_info = None
        next_video_order_number = self.viewing_video_info.get("video_order_number") + 1
        if len(self.lessons) == next_video_order_number:
            return False
        for lesson in self.lessons:
            if lesson.get("video_order_number") == next_video_order_number:
                next_video_info = lesson
                break
        if not next_video_info:
            raise Exception("无法切换下一个视频：下一个视频为空")
        self.viewing_video_info = next_video_info