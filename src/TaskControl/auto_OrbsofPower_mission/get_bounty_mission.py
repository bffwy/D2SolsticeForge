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
from settings import mission_settings, mission_color_settings
from utils import d2_operation
from PIL import ImageGrab
from enum import Enum


class ColorStatus(Enum):
    GREEN = "绿色悬赏"
    GRAY_GREEN = "灰绿色悬赏"
    OTHER = "其他悬赏"


next_page_button_pos = mission_settings.next_page_button_pos
refresh_time = mission_settings.refresh_time

refresh_pos_x = mission_settings.refresh_pos_x
refresh_pos_y = mission_settings.refresh_pos_y

min_radius = mission_settings.min_radius
max_radius = mission_settings.max_radius
y_diff = mission_settings.y_diff
x_range = mission_settings.x_range
perfect_like = mission_settings.perfect_like

REFRESH_LEAVE = 5
GET_MISSION_LEAVE = 2

gray_green_range = mission_color_settings.gray_green_range
green_range = mission_color_settings.green_range
check_pixel_offset = mission_color_settings.check_pixel_offset


def is_in_range(pixel, range1, range2):
    for p, r1, r2 in zip(pixel, range1, range2):
        if not r1 <= p <= r2:
            return False
    return True


def get_color_status(screen_shot, center_x, center_y):
    color_status_counts = {ColorStatus.GRAY_GREEN: 0, ColorStatus.GREEN: 0, ColorStatus.OTHER: 0}
    for pixel_pos in check_pixel_offset:
        pix = screen_shot.getpixel((center_x + pixel_pos[0], center_y + pixel_pos[1]))
        print(f"{pixel_pos}: 像素值: {pix}")
        if is_in_range(pix, gray_green_range[0], gray_green_range[1]):
            color_status_counts[ColorStatus.GRAY_GREEN] += 1
        elif is_in_range(pix, green_range[0], green_range[1]):
            color_status_counts[ColorStatus.GREEN] += 1
        else:
            color_status_counts[ColorStatus.OTHER] += 1

    # 返回出现次数最多的颜色状态
    return max(color_status_counts, key=color_status_counts.get)


def get_index_by_pos(x_pos, y_pos):
    index_x = index_y = None
    for i, pos in enumerate(x_range):
        if pos - y_diff <= x_pos <= pos + y_diff:
            index_x = i
            break

    for i, pos in enumerate(refresh_pos_y):
        if pos - y_diff <= y_pos <= pos + y_diff:
            index_y = i
            break
    return index_x, index_y


def click_pos(x, y):
    find_pos = x, y
    d2_operation.d2_move(*find_pos)
    time.sleep(0.5)
    pydirectinput.click()
    time.sleep(0.5)


def click_by_index(x_index, y_index):
    click_pos_x = x_range[x_index]
    click_pos_y = refresh_pos_y[y_index]
    click_pos(click_pos_x, click_pos_y)


def get_current_page_mission(page_index):
    bbox = d2_operation.get_d2_box()
    screenshot = ImageGrab.grab(bbox=bbox)
    image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    # image = get_screen_shot()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_blurred = cv2.GaussianBlur(gray, (9, 9), 0)
    circles = cv2.HoughCircles(
        gray_blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=30,
        param1=50,
        param2=perfect_like,
        minRadius=min_radius,
        maxRadius=max_radius,
    )
    find_index_and_pos = defaultdict(list)
    if circles is not None:
        circles = np.uint16(np.around(circles))
        # 先不二次检测 看看情况
        for i in circles[0, :]:
            center_x, center_y = int(i[0]), int(i[1])
            x_index, y_index = get_index_by_pos(center_x, center_y)
            color_status = get_color_status(screenshot, center_x, center_y)
            if x_index is None or y_index is None:
                continue
            print(
                f"第 {page_index+1} 页;第 {x_index+1} 行 第 {y_index+1} 列的圆 半径：{int(i[2])} 位置:{center_x}, {center_y},, 颜色:{color_status.value}"
            )
            find_index_and_pos[y_index].append((center_x, center_y, color_status))
    return find_index_and_pos


def refresh_mission(require_index):
    for i in require_index:
        y_pos = refresh_pos_y[i]
        d2_operation.d2_move(refresh_pos_x, y_pos)
        time.sleep(0.5)
        pydirectinput.mouseDown()
        time.sleep(3)
        pydirectinput.mouseUp()
    # 不要挡住图像识别
    d2_operation.d2_move(x_range[1] + 100, refresh_pos_y[2] + 100)
    time.sleep(0.5)


def re_get_page_mission(page_index, force_refresh=False):
    require_index = [0, 1, 2]
    if page_index == 1:
        require_index = [0, 1]
    get_mission_index = {i: False for i in require_index}
    use_leave = 0
    get_mission_num = 0
    current_refresh_time = refresh_time
    max_time = 100
    while True and max_time > 0:
        max_time -= 1
        find_index_and_pos = get_current_page_mission(page_index)
        if find_index_and_pos:
            for y_index, items in find_index_and_pos.items():
                # items.sort(key=lambda x: x[0], reverse=True)
                items.sort(key=lambda x: (x[1], -x[0]))
                if get_mission_index[y_index]:
                    continue
                get_mission_index[y_index] = True
                find_pox_x, find_pox_y, color_status = items[0]
                if color_status != ColorStatus.GREEN:
                    # 不是绿悬赏
                    continue
                click_pos(find_pox_x, find_pox_y)
                use_leave += GET_MISSION_LEAVE
                get_mission_num += 1

        need_refresh_index = [i for i in require_index if not get_mission_index[i]]
        if not need_refresh_index:
            break

        if current_refresh_time <= 0 and not force_refresh:
            break
        refresh_mission(need_refresh_index)
        use_leave += REFRESH_LEAVE * len(need_refresh_index)

        current_refresh_time -= 1

    # 保底白悬赏
    if mission_settings.get_white_mission:
        for i in require_index:
            if not get_mission_index[i]:
                click_by_index(0, i)
                use_leave += 1
                get_mission_num += 1

    return use_leave, get_mission_num


def _get_mission():
    do_actions("打开至日熔炉界面")
    time.sleep(2)
    use_leave, get_mission_num = re_get_page_mission(0)
    time.sleep(1)
    d2_operation.d2_move(*next_page_button_pos)
    time.sleep(0.5)
    print(f"下一页")
    pydirectinput.click()
    time.sleep(1)
    use_leave_2, get_mission_num_2 = re_get_page_mission(1)
    use_leave += use_leave_2
    get_mission_num += get_mission_num_2

    print(f"使用银叶 {use_leave}, 获取任务 {get_mission_num} 个")
    if get_mission_num == 0:
        use_leave_3, get_mission_num_2 = re_get_page_mission(1, force_refresh=True)
        use_leave += use_leave_3

    pydirectinput.press("escape")
    time.sleep(1)
    pydirectinput.press("escape")
    time.sleep(1)
    return use_leave


def get_mission():
    use_leave = _get_mission()
    return use_leave


# d2_operation.active_window()
# print(get_mission())
# print(re_get_page_mission(0))
# print(get_current_page_mission())
