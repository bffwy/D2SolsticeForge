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
from TaskControl.ActControl import do_actions
from screenshot import grab_image
from settings import other_settings

use_dim = other_settings.use_dim
update_interval = 5 * 60
LEAVES_ITEM_HASH = 1644922223

bbox = other_settings.check_box

ocr = ddddocr.DdddOcr()


def timer_update_item_quantity():
    get_profile_inventory()


if use_dim and False:
    timer_update_item_quantity()
    timeout_id = TimerManager.add_timer(update_interval, timer_update_item_quantity, repeat=True)


def get_leaves_item_quantity():
    if use_dim and False:
        return get_item_quantity(LEAVES_ITEM_HASH)
    do_actions("定位到有银叶数量界面")
    image = grab_image(bbox=bbox)
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    result = ocr.classification(image_bytes.getvalue())
    do_actions("回退到检测前界面")
    time.sleep(1)

    try:
        return int(result)
    except Exception:
        return 0


# from utils import d2_operation

# d2_operation.active_window()

# print(get_leaves_item_quantity())
