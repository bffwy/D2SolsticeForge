# -*- coding: utf-8 -*-

import os
import sys

parent_dir_name = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir_name)
sys.path.append(os.path.dirname(parent_dir_name))
sys.path.append(os.path.dirname(os.path.dirname(parent_dir_name)))

import cv2
import time
import pydirectinput
import numpy as np
from screenshot import get_screen_shot
from collections import defaultdict
from TaskControl.ActControl import do_actions
from settings import mission_settings

next_page_button_pos = mission_settings.next_page_button_pos
refresh_time = mission_settings.refresh_time

refresh_pos_x = mission_settings.refresh_pos_x
refresh_pos_y = mission_settings.refresh_pos_y
x_range = mission_settings.x_range

min_radius = mission_settings.min_radius
max_radius = mission_settings.max_radius
y_diff = mission_settings.y_diff

REFRESH_LEAVE = 5
GET_MISSION_LEAVE = 2


def get_index_by_y_pos(x_pos, y_pos):
    x_check = x_range[0] <= x_pos <= x_range[1]
    if not x_check:
        return

    for i, pos in enumerate(refresh_pos_y):
        if pos - y_diff <= y_pos <= pos + y_diff:
            return i


def get_current_page_mission():
    image = get_screen_shot()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_blurred = cv2.GaussianBlur(gray, (9, 9), 0)
    circles = cv2.HoughCircles(
        gray_blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=20,
        param1=50,
        param2=30,
        minRadius=min_radius,
        maxRadius=max_radius,
    )
    find_index_and_pos = defaultdict(list)
    if circles is not None:
        circles = np.uint16(np.around(circles))
        # 先不二次检测 看看情况
        for i in circles[0, :]:
            center_x, center_y = int(i[0]), int(i[1])
            y_index = get_index_by_y_pos(center_x, center_y)
            print(f"find line: {y_index} pos:{center_x}, {center_y}")
            if y_index is not None:
                find_index_and_pos[y_index].append([center_x, center_y])
    return find_index_and_pos


def refresh_mission(require_index):
    for i in require_index:
        y_pos = refresh_pos_y[i]
        pydirectinput.moveTo(refresh_pos_x, y_pos)
        time.sleep(0.5)
        pydirectinput.mouseDown()
        time.sleep(3)
        pydirectinput.mouseUp()
    # 不要挡住图像识别
    pydirectinput.moveTo(1, 1)
    time.sleep(0.5)


def re_get_page_mission(page_index):
    require_index = [0, 1, 2]
    if page_index == 1:
        require_index = [0, 1]
    get_mission_index = {i: False for i in require_index}
    use_leave = 0

    current_refresh_time = refresh_time
    while current_refresh_time > 0:
        current_refresh_time -= 1
        find_index_and_pos = get_current_page_mission()
        for index in find_index_and_pos:
            if get_mission_index[index]:
                continue
            get_mission_index[index] = True

            find_pos = find_index_and_pos[index][0]
            pydirectinput.moveTo(*find_pos)
            time.sleep(0.5)
            pydirectinput.click()
            time.sleep(0.5)
            use_leave += GET_MISSION_LEAVE

        need_refresh_index = [i for i in require_index if not get_mission_index[i]]
        if not need_refresh_index:
            break
        use_leave += REFRESH_LEAVE * len(need_refresh_index)
        refresh_mission(need_refresh_index)

    return use_leave


def get_mission():
    do_actions("打开至日熔炉界面")
    time.sleep(2)
    use_leave = re_get_page_mission(0)
    time.sleep(1)
    pydirectinput.moveTo(*next_page_button_pos)
    time.sleep(0.5)
    pydirectinput.click()
    time.sleep(1)
    use_leave += re_get_page_mission(1)
    pydirectinput.press("escape")
    time.sleep(1)
    pydirectinput.press("escape")
    time.sleep(1)
    return use_leave


# from utils import d2_operation

# d2_operation.active_window()
# time.sleep(2)
# print(re_get_page_mission(1))
