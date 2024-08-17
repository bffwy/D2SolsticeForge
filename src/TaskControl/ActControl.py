import json
import time
import threading
import pydirectinput
import os
import sys
from copy import deepcopy

parent_dir_name = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir_name)
sys.path.append(os.path.dirname(parent_dir_name))

from settings import mode
from utils import path_helper
from utils import d2_operation
from utils.patterns import Singleton
from TaskControl.Base.CommonLogger import my_logger
from my_window.MainWindow import log_window

pydirectinput.PAUSE = 0


class ConfigManager(Singleton):
    def __init__(self):
        self.configs = {}
        self.action_map = {}
        self.load_action_map()

    def load_action_map(self):
        base_path = path_helper.get_config("act")
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".json"):
                    action_name = os.path.splitext(file)[0]
                    self.action_map[action_name] = os.path.join(root, file)

    def get_config(self, action_name):
        if action_name not in self.configs:
            file_path = self.action_map.get(action_name)
            if file_path is None:
                return None
            self.configs[action_name] = self.load_config(file_path)
        return self.configs[action_name]

    def load_config(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config


def execute_action(action):
    my_logger.debug(f"execute_action: {action}")
    if action["type"] == "key":
        is_in_bind_key_chn = action["name"] in d2_operation.bind_key_chn
        if is_in_bind_key_chn:
            d2_operation.key_down_chn(action["name"])
        else:
            pydirectinput.keyDown(action["name"])
        time.sleep(action["duration"])
        if is_in_bind_key_chn:
            d2_operation.key_up_chn(action["name"])
        else:
            pydirectinput.keyUp(action["name"])

    elif action["type"] == "mouse_move":
        if action.get("relative"):
            pydirectinput.move(*action["relative"], relative=True)

        elif action.get("absolute"):
            pos = action["absolute"]
            pos = d2_operation.get_d2_position(pos)
            pydirectinput.moveTo(*pos)

    elif action["type"] == "wait":
        time.sleep(action["duration"])

    elif action["type"] == "leftClick":
        pydirectinput.click(button="left")
    elif action["type"] == "rightClick":
        pydirectinput.click(button="right")

    elif action["type"] == "mouseDown":
        pydirectinput.mouseDown(button=action["key"])
    elif action["type"] == "mouseUp":
        pydirectinput.mouseUp(button=action["key"])

    elif action["type"] == "press":
        if action["key"] in d2_operation.bind_key_chn:
            d2_operation.key_down_chn(action["key"], click=True)
        else:
            pydirectinput.press(action["key"])


# def _actions(config):
#     for action in config["actions"]:
#         if action.get("blocking", False):
#             execute_action(action)
#         else:
#             threading.Thread(target=execute_action, args=(action,)).start()


class ActionThread(threading.Thread):
    def __init__(self, action):
        super(ActionThread, self).__init__()
        self.action = action
        self.stop_event = threading.Event()

    def run(self):
        if not self.stop_event.is_set():
            execute_action(self.action)

    def stop(self):
        self.stop_event.set()


class ThreadManager:
    def __init__(self):
        self.current_threads = []

    def add_thread(self, thread):
        self.current_threads.append(thread)

    def stop_all(self):
        for thread in self.current_threads:
            thread.stop()
        self.current_threads = []


thread_manager = ThreadManager()


def _actions(config):
    threads = []
    for action in config["actions"]:
        if action.get("blocking", False):
            execute_action(action)
        else:
            thread = ActionThread(action)
            thread.start()
            threads.append(thread)
            thread_manager.add_thread(thread)
    return threads


def stop_all():
    thread_manager.stop_all()


def do_actions(action_name):
    if mode.is_1280_resolution:
        action_name = f"{action_name}_1280"
    config = ConfigManager().get_config(action_name)
    if config is None:
        my_logger.info(f"actions NotFound: {action_name}")
        raise Exception(f"actions NotFound: {action_name}")
    my_logger.info(f"开始执行act {action_name}")
    log_window.emit_log(f"开始执行act {action_name}")
    _actions(config)
    # log_window.emit_log(f"执行结束act {action_name}")


def esc_once():
    pydirectinput.press("esc")
    time.sleep(1)


def enter():
    pydirectinput.press("enter")
    time.sleep(1)


def convert_coordinates(original_coordinates):
    # 使用示例
    original_resolution = [1920, 1080]
    new_resolution = [1280, 720]

    # 计算缩放比例
    scale = [new / original for new, original in zip(new_resolution, original_resolution)]
    # 转换坐标
    new_coordinates = [int(original * scale) for original, scale in zip(original_coordinates, scale)]
    return new_coordinates


# used_action = set()
# for action_name, file_path in ConfigManager().action_map.items():
#     actions = ConfigManager().get_config(action_name)
#     copy_action = deepcopy(actions)
#     for action in copy_action["actions"]:
#         if "absolute" in action:
#             pos = action["absolute"]
#             new_coordinates = convert_coordinates(pos)
#             action["absolute"] = new_coordinates
#     # 生成新的文件路径
#     base, ext = os.path.splitext(file_path)
#     new_file_path = f"{base}_1280{ext}"

#     # 将copy_action保存到新的文件中
#     with open(new_file_path, "w", encoding="utf-8") as f:
#         json.dump(copy_action, f, ensure_ascii=False)

#     key = action["key"]
#     used_action.add(key)

# elif action.get("type") == "key":
#     key = action["name"]
#     used_action.add(key)

# print(used_action)

# d2_operation.active_window()
# do_actions("定位到有银叶数量界面任务2")


# # time.sleep(1)
# do_actions("技能循环")
# # do_actions("PM占点")
# do_actions("走到固定位置")
# times = 5
# while times > 0:
#     times -= 1
#     do_actions("技能循环")
# do_actions("3号位武器自杀")
