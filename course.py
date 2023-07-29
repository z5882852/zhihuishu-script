"""
智慧树课程模块
"""
import json
import time
import urllib

import requests
from urllib.parse import unquote
from utils.encrypt import encrypt_params
from utils.logger import Logger


class QueryCourse:
    def __init__(self, session, logger):
        self.session = session
        self.logger = logger
        self.uuid = None
        self.headers = {}
        self.__headers()
        self.__get_uuid()

    def __headers(self):
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://onlineweb.zhihuishu.com",
            "Pragma": "no-cache",
            "Referer": "https://onlineweb.zhihuishu.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183",
            "sec-ch-ua": "\"Not/A)Brand\";v=\"99\", \"Microsoft Edge\";v=\"115\", \"Chromium\";v=\"115\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\""
        }

    def __get_uuid(self):
        cookies = requests.utils.dict_from_cookiejar(self.session.cookies)
        if not ("CASLOGC" in cookies):
            return
        user_info = cookies.get("CASLOGC", None)
        try:
            self.uuid = json.loads(unquote(user_info)).get("uuid", None)
        except:
            pass

    def query_share_sourse(self, status=0):
        """
        查询共享课
        :param status: 0进行中|1已完成
        """
        url = "https://onlineservice-api.zhihuishu.com/gateway/t/v1/student/course/share/queryShareCourseInfo"
        data = {
            "secretStr": encrypt_params({
                "status": status,
                "pageNo": 1,
                "pageSize": 10
            }, "COURSE_AES_KEY"),
            "date": int(time.time())
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            print(f"查询共享课失败，status_code: {response.status_code}")
            return []
        data = response.json()
        if data.get("code", 500) != 200:
            print(f"查询共享课失败，result_code: {data.get('code', 500)}")
            return []
        course_list = data.get("result", {}).get("courseOpenDtos", None)
        if not course_list:
            print(f"共享课内容为空")
            return []
        return course_list

    def query_micro_course(self):
        """查询校内学分课"""
        url = "https://onlineservice-api.zhihuishu.com/gateway/t/v1/student/course/share/queryMicroCourseInfo"
        data = {
            "secretStr": encrypt_params({
                "pageNo": 1,
                "pageSize": 10
            }, "COURSE_AES_KEY"),
            "date": int(time.time())
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            print(f"查询校内学分课失败，status_code: {response.status_code}")
            return []
        data = response.json()
        if data.get("code", 500) != 200:
            print(f"查询校内学分课失败，result_code: {data.get('code', 500)}")
            return []
        course_list = data.get("result", {}).get("courseOpenDtos", None)
        if not course_list:
            print(f"校内学分课内容为空")
            return []
        return course_list

    def query_2C_course(self):
        """查询兴趣课"""
        if not self.uuid:
            print("无法获取用户UUID!")
            return []
        url = "https://b2cpush.zhihuishu.com/b2cpush/courseDetail/query2CCourseList"
        data = {
            "pageNum": "1",
            "pageSize": "10",
            "uuid": self.uuid,
            "date": "2023-07-25T17:39:51.676Z"
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            print(f"查询兴趣课失败，status_code: {response.status_code}")
            return []
        data = response.json()
        if data.get("status", 500) != "200":
            print(f"查询兴趣课失败，result_code: {data.get('status', 500)}")
            return []
        if not data.get("rt", None):
            print(f"兴趣课内容为空")
            return []
        course_list = data.get("rt", {}).get("dataList", None)
        if not course_list:
            print(f"兴趣课内容为空")
            return []
        return course_list

    def query_student_AI_course(self):
        """查询兴趣课"""
        url = "https://onlineservice-api.zhihuishu.com/gateway/t/v1/student/queryStudentAICourseList"
        data = {
            "secretStr": encrypt_params({
                "status": 3
            }, "COURSE_AES_KEY"),
            "date": int(time.time())
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            print(f"查询AI课失败，status_code: {response.status_code}")
            return []
        data = response.json()
        if data.get("status", 500) != "200":
            print(f"查询AI课失败，result_code: {data.get('status', 500)}")
            return []
        if not data.get("rt", None):
            print(f"AI课内容为空")
            return []
        course_list = data.get("rt", {}).get("dataList", None)
        if not course_list:
            print(f"AI课内容为空")
            return []
        return course_list


class ShareCourse:
    def __init__(self, session):
        self.session = session
        self.headers = {}
        self.__headers()

    def __headers(self):
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://studyvideoh5.zhihuishu.com",
            "Pragma": "no-cache",
            "Referer": "https://studyvideoh5.zhihuishu.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183",
            "sec-ch-ua": "\"Not/A)Brand\";v=\"99\", \"Microsoft Edge\";v=\"115\", \"Chromium\";v=\"115\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\""
        }

    def go_login(self, go_link):
        """
        登录共享学分课视频页面，否则会出现code: 500错误
        """
        params = {
            "fromurl": go_link
        }
        url = "https://studyservice-api.zhihuishu.com/login/gologin"
        self.session.get(url, params=params)

    def query_course_info(self, recruit_and_course_id):
        """
        查询课程信息
        :param recruit_and_course_id:
        :return: 课程信息, 主要内容:
        "data":{
            "classId": 课程id,
            "schoolId": 学校id,
            "recruitId": ,
            "courseInfo": {
                "courseId": 课程id,
                "name": 课程名称,
                "schoolName“: 学习名称
            },
            "studyStatus": 学习状态
        }
        """
        url = "https://studyservice-api.zhihuishu.com/gateway/t/v1/learning/queryCourse"
        timestamp = int(time.time()) * 1000
        data = {
            "secretStr": encrypt_params({
                "recruitAndCourseId": recruit_and_course_id,
                "dateFormate": timestamp
            }, "STUDY_AES_KEY"),
            "dateFormate": str(timestamp)
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            raise Exception(f"查询课程信息失败，status_code: {response.status_code}")
        data = response.json()
        if data.get("code", -1) != 0:
            raise Exception(f"查询课程信息失败，response_code: {data.get('code', -1)}")
        return data.get("data", None)

    def get_video_list(self, recruit_and_course_id):
        """
        获取课程视频列表
        :param recruit_and_course_id:
        :return: 课程视频列表
        "data": {
            "recruitId": 184020,
            "courseId": 1000072747,
            "videoChapterDtos": [
                {
                    "id": 1001061211, #章节id
                    "name": "绪论",
                    "videoLessons": [
                        {
                            "id": 1001234967, # 课id
                            "name": "工程与地质的联系",
                            "videoSmallLessons": [
                                {
                                    "id": 1001118200, #视频课id
                                    "name": "工程地质经验教训",
                                    "orderNumber": 1,
                                    "videoId": 38700733, #视频id
                                    "videoSec": 837, #视频总长度(s)
                                    "isStudiedLesson": 0
                                },
                                ...
                            ],
                            "isStudiedLesson": 0
                        },
                        ...
                    ],
                    "isPass": 1,
                    "studentExamDto": {
                        # 测试信息
                    }
                },
                ...
            ]
        """
        url = "https://studyservice-api.zhihuishu.com/gateway/t/v1/learning/videolist"
        timestamp = int(time.time()) * 1000
        data = {
            "secretStr": encrypt_params({
                "recruitAndCourseId": recruit_and_course_id,
                "dateFormate": timestamp
            }, "STUDY_AES_KEY"),
            "date": timestamp
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            raise Exception(f"获取课程视频列表失败，status_code: {response.status_code}")
        data = response.json()
        if data.get("code", -1) != 0:
            raise Exception(f"获取课程视频列表失败，response_code: {data.get('code', -1)}")
        return data.get("data", None)

    def query_study_info(self, lessonIds, lessonVideoIds, recruitId):
        """
        查询学习信息
        :param lessonIds: list[int] 课id列表
        :param lessonVideoIds: list[int] 视频id列表
        :param recruitId: int
        :return: {
            "data": {
                "lesson": {
                    "1001234973": {
                        "studyTotalTime": 0,
                        "watchState": 0
                    },
                    ...
                },
                "lv": {
                    "1001118219": {
                        "studyTotalTime": 0,
                        "watchState": 0
                    },
                    ...
                }
            }
        }
        """
        url = "https://studyservice-api.zhihuishu.com/gateway/t/v1/learning/queryStuyInfo"
        timestamp = int(time.time()) * 1000
        data = {
            "secretStr": encrypt_params({
                "lessonIds": lessonIds,
                "lessonVideoIds": lessonVideoIds,
                "recruitId": recruitId,
                "dateFormate": timestamp
            }, "STUDY_AES_KEY"),
            "date": timestamp
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            raise Exception(f"查询课程信息失败，status_code: {response.status_code}")
        data = response.json()
        if data.get("code", -1) != 0:
            raise Exception(f"查询课程信息失败，response_code: {data.get('code', -1)}")
        return data.get("data", None)

    def query_user_recruit_id_last_video_id(self, recruit_id):
        """
        查询上一次观看的视频ID
        :param recruit_id: int
        :return: {
            "code": 0,
            "message": "请求成功",
            "data": {
                "lastViewVideoId": 39801121
            }
        }
        """
        url = "https://studyservice-api.zhihuishu.com/gateway/t/v1/learning/queryUserRecruitIdLastVideoId"
        timestamp = int(time.time()) * 1000
        data = {
            "secretStr": encrypt_params({
                "recruitId": recruit_id,
                "dateFormate": timestamp
            }, "STUDY_AES_KEY"),
            "date": timestamp
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            raise Exception(f"查询上一次观看的视频ID失败，status_code: {response.status_code}")
        data = response.json()
        if data.get("code", -1) != 0:
            raise Exception(f"查询上一次观看的视频ID失败，response_code: {data.get('code', -1)}")
        return data.get("data", None)

    def query_pre_learning_note(self, ccCourseId, chapterId, lessonId, recruitId, videoId, small_lesson_id=None):
        """
        查询具体视频课程的学习信息
        :param ccCourseId: int 课程id
        :param chapterId: int 章节id
        :param lessonId: int 课id
        :param recruitId: int recruitId
        :param videoId: int 视频id
        :param small_lesson_id: int 视频课id
        :return: learningTokenId需要Base64编码的ID, 已学时间等关于该视频的状态
        "data": {
            "isSlide": false,
            "studiedLessonDto": {
                "id": 8538910234,
                "userId": null,
                "lastStudyTime": null,
                "isDeteled": null,
                "updateTime": null,
                "createTime": null,
                "learnTime": "00:00:00",
                "learnTimeSec": 0,
                "isStudiedLesson": 0,
                "studyTotalTime": 0,
                "studyPercent": null,
                "watchState": 2,
                "videoSize": 0.0,
                "sourseType": null,
                "watchCount": null,
                "playTimes": null,
                "videoId": null,
                "recruitId": null,
                "lessonId": null,
                "lessonVideoId": null,
                "chapterId": null,
                "personalCourseId": null
            }
        }
        """
        url = 'https://studyservice-api.zhihuishu.com/gateway/t/v1/learning/prelearningNote'
        timestamp = int(time.time()) * 1000
        form_data = {
            "ccCourseId": ccCourseId,
            "chapterId": chapterId,
            "isApply": 1,
            "lessonId": lessonId,
            "recruitId": recruitId,
            "videoId": videoId,
            "dateFormate": timestamp
        }
        if small_lesson_id:
            form_data["lessonVideoId"] = small_lesson_id
        data = {
            "secretStr": encrypt_params(form_data, "STUDY_AES_KEY"),
            "date": timestamp
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            raise Exception(f"查询具体视频课程的学习信息失败，status_code: {response.status_code}")
        data = response.json()
        if data.get("code", -1) != 0:
            raise Exception(f"查询具体视频课程的学习信息失败，response_code: {data.get('code', -1)}")
        return data.get("data", None)

    def get_video_pointer_info(self, lessonId, recruitId, courseId, small_lesson_id=None):
        """
        获取视频额外内容检查点
        :param lessonId: int 课id
        :param recruitId: int recruitId
        :param courseId: int 课程id
        :param small_lesson_id: int 视频课id
        :return: dict
        "data": {
                "videoThemeDtos": null,
                "popupPictureDtos": [],
                "questionPoint": [
                    {
                        "timeSec": 180,
                        "questionIds": "895149624"
                    }
                ],
                "knowledgeCardDtos": null
            }
        }
        """
        url = "https://studyservice-api.zhihuishu.com/gateway/t/v1/popupAnswer/loadVideoPointerInfo"
        timestamp = int(time.time())*1000
        form_data = {
            "lessonId": lessonId,
            "recruitId": recruitId,
            "courseId": courseId,
            "dateFormate": timestamp
        }
        if small_lesson_id:
            form_data["lessonVideoId"] = small_lesson_id
        data = {
            "secretStr": encrypt_params(form_data, "STUDY_AES_KEY"),
            "date": timestamp
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            raise Exception(f"获取视频额外内容检查点失败，status_code: {response.status_code}")
        data = response.json()
        if data.get("code", -1) != 0:
            raise Exception(f"获取视频额外内容检查点失败，response_code: {data.get('code', -1)}")
        return data.get("data", None)

    def get_popup_exam(self, lessonId, questionIds, small_lesson_id=None):
        """
        获取弹题数据
        :param lessonId:
        :param questionIds:
        :param small_lesson_id:
        :return: dict
        "data": {
            "lessonTestQuestionUseInterfaceDtos": [
                {
                    "id": null,
                    "testQuestion": {
                        "inputType": 2,
                        "name": "下列关于三峡大坝修筑难点的表述正确的是（ ）。",
                        "questionId": 895149624,
                        "questionOptions": [
                            {
                                "id": 124001834,
                                "content": " 三峡大坝的修筑面临复杂的地质条件问题<br>",
                                "sort": 1,
                                "result": "1",
                                "acount": null
                            },
                            ...
                        ],
                        "questionType": {
                            "id": 2,
                            "name": "多选题",
                            "inputType": "checkbox"
                        },
                        "videoInfo": [],
                        "imgUrls": [],
                        "txtInfo": null
                    },
                    "analysis": null,
                    "datas": null,
                    "data": null,
                    "zAnswer": null
                }
            ]
        }
        """
        url = "https://studyservice-api.zhihuishu.com/gateway/t/v1/popupAnswer/lessonPopupExam"
        timestamp = int(time.time()) * 1000
        form_data = {
            "lessonId": lessonId,
            "questionIds": questionIds,
            "dateFormate": timestamp
        }
        if small_lesson_id:
            form_data["lessonVideoId"] = small_lesson_id
        data = {
            "secretStr": encrypt_params(form_data, "STUDY_AES_KEY"),
            "date": timestamp
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            raise Exception(f"获取弹题数据失败，status_code: {response.status_code}")
        data = response.json()
        if data.get("code", -1) != 0:
            raise Exception(f"获取弹题数据失败，response_code: {data.get('code', -1)}")
        return data.get("data", None)

    def submit_popup_exam(self, courseId, recruitId, testQuestionId, lessonId, answer, isCurrent, small_lesson_id=None):
        """
        提交弹题答案
        :param courseId: int 课程id
        :param recruitId: int recruitId
        :param testQuestionId: int 问题id
        :param lessonId: int 课id
        :param answer: str 答案 (例如单选:"124001834", 多选:"124001834,124001835")
        :param isCurrent: str 是否正确 (例如正确:"1", 错误:"0")
        :param small_lesson_id:
        :return: dict
        "data": {
                "submitStatus": true
        }
        """
        url = "https://studyservice-api.zhihuishu.com/gateway/t/v1/popupAnswer/saveLessonPopupExamSaveAnswer"
        timestamp = int(time.time()) * 1000
        form_data = {
            "courseId": courseId,
            "recruitId": recruitId,
            "testQuestionId": testQuestionId,
            "lessonId": lessonId,
            "answer": answer,
            "isCurrent": isCurrent,
            "testType": 0,
            "dateFormate": timestamp
        }
        if small_lesson_id:
            form_data["lessonVideoId"] = small_lesson_id
        data = {
            "secretStr": encrypt_params(form_data, "STUDY_AES_KEY"),
            "date": timestamp
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            raise Exception(f"提交弹题答案失败，status_code: {response.status_code}")
        data = response.json()
        if data.get("code", -1) != 0:
            raise Exception(f"提交弹题答案失败，response_code: {data.get('code', -1)}")
        return data.get("data", None)

    def save_database_interval_time_v2(self, ewssw, sdsew, zwsds, courseId):
        """
        提交视频学习进度
        :param ewssw: str watch_point
        :param sdsew: str ev加密后的值
        :param zwsds: str token_id
        :param courseId: int 课程id
        :return:
        "data": {
            "submitSuccess": true
        }
        """
        url = "https://studyservice-api.zhihuishu.com/gateway/t/v1/learning/saveDatabaseIntervalTimeV2"
        timestamp = int(time.time()) * 1000
        data = {
            "secretStr": encrypt_params({
                "ewssw": ewssw,
                "sdsew": sdsew,
                "zwsds": zwsds,
                "courseId": courseId,
                "dateFormate": timestamp
            }, "STUDY_AES_KEY"),
            "date": timestamp
        }
        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            raise Exception(f"提交视频学习进度失败，status_code: {response.status_code}, response: {response.text}")
        data = response.json()
        if data.get("code", -1) != 0:
            raise Exception(f"提交视频学习进度失败，response_code: {data.get('code', -1)}, response: {response.text}")
        return data.get("data", None)
