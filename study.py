from course import ShareCourse
from utils.logger import Logger
from utils.utils import get_error_retry


class StudyShareCourse:
    def __init__(self, recruit_and_course_id, session, speed=1.5):
        self.recruit_and_course_id = recruit_and_course_id
        self.speed = speed
        self.recruit_id = None
        self.course_name = None
        self.course_id = None
        self.lesson_ld = None
        self.small_lesson_id = None
        self.video_id = None
        self.chapte_id = None
        self.lessons = []
        self.session = session
        self.ShareCourse = ShareCourse(session)
        self.logger = Logger()
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
        if len(self.lessons) == 0:
            raise Exception("视频列表为空!")