import cv2
import os
import json

import numpy as np
from PIL import ImageGrab, Image
from utils import decorator, path_helper
from datetime import datetime
from functools import lru_cache
from utils import path_helper, d2_operation
from loguru import logger
from itertools import chain
from settings import mode

MONITOR_WIDTH, MONITOR_HEIGHT = ImageGrab.grab().size
logger.info(f"屏幕分辨率: {MONITOR_WIDTH}x{MONITOR_HEIGHT}")


@lru_cache(maxsize=None)
def load_image_cv(image_path):
    try:
        return convert_image_to_open_cv(Image.open(image_path))
    except Exception as e:
        raise Exception(f"加载图片 {image_path} 失败") from e


@lru_cache(maxsize=None)
def load_image_raw(image_path):
    try:
        return cv2.imread(image_path)
    except Exception as e:
        raise Exception(f"加载图片 {image_path} 失败") from e


def compare_hist(img1, img2):
    # 将图像转换为HSV颜色空间
    img1_hsv = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
    img2_hsv = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

    # 计算图像的直方图
    hist1 = cv2.calcHist([img1_hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
    hist2 = cv2.calcHist([img2_hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])

    # 归一化直方图
    cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

    # 计算直方图相似性
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    return similarity


def get_hsv_similarity(grabbed_image, local_image):
    img = cv2.cvtColor(np.asarray(grabbed_image), cv2.COLOR_RGB2BGR)
    return compare_hist(local_image, img)


def convert_image_to_open_cv(image: Image.Image):
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def sharpen_image(image: cv2.typing.MatLike):
    # 创建一个锐化核
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    # 使用filter2D函数进行图像锐化
    sharpened = cv2.filter2D(image, -1, kernel)
    return sharpened


def get_template_similarity_combined(image: Image.Image, template: cv2.typing.MatLike):
    image_cv = convert_image_to_open_cv(image)
    # 对图像和模板进行锐化
    sharpened_image = sharpen_image(image_cv)
    sharpened_template = sharpen_image(template)
    # 使用锐化的图像和模板进行模板匹配
    result_sharpened = cv2.matchTemplate(sharpened_image, sharpened_template, cv2.TM_CCOEFF_NORMED)
    min_val_sharpened, max_val_sharpened, min_loc_sharpened, max_loc_sharpened = cv2.minMaxLoc(result_sharpened)
    # 使用原始的图像和模板进行模板匹配
    result_original = cv2.matchTemplate(image_cv, template, cv2.TM_CCOEFF_NORMED)
    min_val_original, max_val_original, min_loc_original, max_loc_original = cv2.minMaxLoc(result_original)
    # 返回两种方法中相似度最大的那个
    return max(max_val_sharpened, min_val_original)


def get_template_similarity(image: Image.Image, template: cv2.typing.MatLike):
    image_cv = convert_image_to_open_cv(image)
    # 对图像和模板进行锐化
    image_cv = sharpen_image(image_cv)
    template = sharpen_image(template)
    result = cv2.matchTemplate(image_cv, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val


def get_mask_ratio(image: np.ndarray, lower_bound: np.ndarray, upper_bound: np.ndarray):
    mask = cv2.inRange(image, lower_bound, upper_bound)
    return np.sum(mask == 255) / (image.size / 3)


# @decorator.timer_log
def grab_image(bbox):
    return ImageGrab.grab(bbox=bbox)


def get_path_by_screen_size(path):
    return f"./asset/{path}.png"
    MONITOR_WIDTH, MONITOR_HEIGHT = ImageGrab.grab().size
    return f"./asset/{path}_{MONITOR_WIDTH}.png"


def get_crop_path(path):
    return f"./asset/{path}.png"


def check_bbox(bbox):
    if len(bbox) != 4:
        return False
    for i, coordinate in enumerate(bbox):
        if not isinstance(coordinate, int):
            return False
        if coordinate < 0:
            return False
        if i % 2 == 0 and coordinate > MONITOR_WIDTH:
            print(f"{coordinate}:{MONITOR_WIDTH}")
            return False
        elif i % 2 == 1 and coordinate > MONITOR_HEIGHT:
            print(f"{coordinate}:{MONITOR_HEIGHT}")
            return False
    return True


def get_similarity(path, bbox, debug):
    real_path = get_path_by_screen_size(path)
    if not os.path.exists(real_path):
        raise Exception(f"{real_path} 不存在, 影响到正常功能")
    image_cv = load_image_cv(real_path)
    # image_raw = load_image_raw(real_path)
    ori_box = bbox.copy()
    bbox = d2_operation.get_d2_box(ori_box)
    grabbed_image = grab_image(bbox)
    ret = get_template_similarity_combined(grabbed_image, image_cv)
    if debug:
        time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        file_name = f"{path}_{time_str}_相似度{ret:.2f}.png"
        logger.debug(f"Debug 保存图片: {file_name}")
        if not os.path.exists("./debug"):
            os.makedirs("./debug")
        grabbed_image.save(f"./debug/{file_name}")
    logger.debug(f"check_path: {path} 相似度: {ret:.2f}")
    return ret


def check_boss_exit(conf=0.6, save=False):
    from utils.yolov8Util import get_boss_result

    image = ImageGrab.grab(all_screens=True)
    return get_boss_result(image, conf, save=save)


def test_get_image(bbox):
    x, y, x1, y1 = bbox
    x, y = d2_operation.back_2_d2_pos(x, y)
    x1, y1 = d2_operation.back_2_d2_pos(x1, y1)

    image = ImageGrab.grab(bbox)
    file_name = f"{x},{y},{x1},{y1}.png"
    image.save(f"./debug/{file_name}")
    return image


def crop_image(image_path, path_name, bbox):
    image = Image.open(image_path)
    cropped_image = image.crop(bbox)
    save_path = get_path_by_screen_size(path_name)
    print(f"crop_image: {save_path} 保存成功")
    cropped_image.save(save_path)


def init_image():
    file_path = path_helper.get_config(mode.task_config)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        for key, task_config in config.items():
            if "check_image" in task_config and "check_box" in task_config:
                path_name = task_config["check_image"]
                bbox = task_config["check_box"]
                real_path = get_path_by_screen_size(path_name)
                if not os.path.exists(real_path):
                    crop_path = get_crop_path(path_name)
                    if os.path.exists(crop_path):
                        crop_image(crop_path, path_name, bbox)


def get_image_box():
    d = {}
    file_path = path_helper.get_config(mode.task_config)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        for task_name, task_config in config.items():
            if "check_box" not in task_config:
                continue
            bbox = task_config["check_box"]
            d[task_name] = bbox
    return d


def get_screen_shot(bbox=None):
    import time

    if bbox is None:
        bbox = d2_operation.get_d2_box()
    screenshot = grab_image(bbox)
    # time_str = time.strftime("%Y-%m-%d_%H-%M-%S")
    # screenshot.save(f"./debug/{time_str}_getmission.png")
    image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    return image


# from utils import d2_operation

# d2_operation.active_window()
# import time
# time.sleep(2)

# bbox = [349, 339, 433, 423]
# test_get_image(bbox)
