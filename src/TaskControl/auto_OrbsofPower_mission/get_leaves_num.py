import os
import sys

parent_dir_name = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir_name)
sys.path.append(os.path.dirname(parent_dir_name))
sys.path.append(os.path.dirname(os.path.dirname(parent_dir_name)))

import time
import io
import ddddocr
from D2API.api import get_item_quantity, get_profile_inventory
from TaskControl.Base.TimerManager import TimerManager
from TaskControl.ActControl import do_actions, esc_once
from screenshot import grab_image
from settings import other_settings, leave_detect
from utils import d2_operation, path_helper

use_dim = other_settings.use_dim
update_interval = 5 * 60
LEAVES_ITEM_HASH = 1644922223


def get_check_bbox():
    item_row_position = leave_detect.item_row_position
    item_column_index = leave_detect.item_column_index

    end_pos = leave_detect.first_box_right_bottom
    bbox_edge = leave_detect.box_edge
    interval = leave_detect.interval
    check_box_range = leave_detect.check_box

    real_end_height = end_pos[1] + ((bbox_edge + interval) * (item_row_position - 1))
    real_end_width = end_pos[0] + ((bbox_edge + interval) * (item_column_index - 1))

    x = real_end_width - check_box_range[0]
    y = real_end_height - check_box_range[1]

    return d2_operation.get_d2_box([x, y, real_end_width, real_end_height])


ocr = ddddocr.DdddOcr()


def timer_update_item_quantity():
    get_profile_inventory()


if use_dim and False:
    timer_update_item_quantity()
    timeout_id = TimerManager.add_timer(update_interval, timer_update_item_quantity, repeat=True)


def get_leaves_item_quantity():
    if use_dim and False:
        return get_item_quantity(LEAVES_ITEM_HASH)
    # d2_operation.key_down_chn("打开物品栏", click=True)
    do_actions("定位到有银叶数量界面")
    # bbox = get_check_bbox()
    pos = [1415, 864, 1475, 890]
    bbox = d2_operation.get_d2_box(pos)
    image = grab_image(bbox=bbox)
    if leave_detect.debug:
        time_str = time.strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"{time_str}_银叶检测.png"
        save_path = path_helper.get_debug(file_name)
        image.save(save_path)
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    result = ocr.classification(image_bytes.getvalue())
    time.sleep(1)
    do_actions("回退到检测前界面")
    # esc_once()
    try:
        return int(result)
    except Exception:
        pass

    return 0


d2_operation.active_window()
print(get_leaves_item_quantity())
