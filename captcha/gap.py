# -*- coding: utf-8 -*-

import cv2
import numpy as np

class SlideCrack(object):
    def __init__(self, gap, bg):
        """
        init code
        :param gap: 缺口图片
        :param bg: 背景图片
        """
        self.gap = gap
        self.bg = bg

    def bytes_to_cv2(self, img, flags=1):
        img_buffer_np = np.frombuffer(img, dtype=np.uint8)
        img_np = cv2.imdecode(img_buffer_np, flags)
        return img_np

    def clear_white(self, img):
        img = self.bytes_to_cv2(img)
        rows, cols, channel = img.shape
        min_x = 255
        min_y = 255
        max_x = 0
        max_y = 0
        for x in range(1, rows):
            for y in range(1, cols):
                t = set(img[x, y])
                if len(t) >= 2:
                    if x <= min_x:
                        min_x = x
                    elif x >= max_x:
                        max_x = x

                    if y <= min_y:
                        min_y = y
                    elif y >= max_y:
                        max_y = y
        img1 = img[min_x:max_x, min_y: max_y]
        return img1

    def template_match(self, tpl, target):
        result = cv2.matchTemplate(target, tpl, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        tl = max_loc
        return tl[0]

    def image_edge_detection(self, img):
        edges = cv2.Canny(img, 100, 200)
        return edges

    def discern(self):
        img1 = self.clear_white(self.gap)

        img1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
        slide = self.image_edge_detection(img1)

        back = self.bytes_to_cv2(self.bg, 0)
        back = self.image_edge_detection(back)

        slide_pic = cv2.cvtColor(slide, cv2.COLOR_GRAY2RGB)
        back_pic = cv2.cvtColor(back, cv2.COLOR_GRAY2RGB)
        x = self.template_match(slide_pic, back_pic)
        # 输出横坐标, 即 滑块在图片上的位置
        return x


def get_gap(img_1, img_2):
    sc = SlideCrack(img_1, img_2)
    return sc.discern()
