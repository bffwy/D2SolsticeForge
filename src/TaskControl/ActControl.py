import json
import time
import threading
import pydirectinput
import os
import sys

parent_dir_name = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir_name)
sys.path.append(os.path.dirname(parent_dir_name))

from utils import path_helper
from utils import d2_operation
from utils.patterns import Singleton
from TaskControl.Base.CommonLogger import my_logger
from screenshot import replace_coordinates

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
            if action.get("base_on_2560"):
                pos = replace_coordinates(pos)
            pydirectinput.moveTo(*pos)

    elif action["type"] == "wait":
        time.sleep(action["duration"])

    elif action["type"] == "click":
        pos = action["absolute"]
        if action.get("base_on_2560"):
            pos = replace_coordinates(pos)
        pydirectinput.click(*pos)

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


def _actions(config):
    for action in config["actions"]:
        if action.get("blocking", False):
            execute_action(action)
        else:
            threading.Thread(target=execute_action, args=(action,)).start()


def do_actions(action_name):
    config = ConfigManager().get_config(action_name)
    if config is None:
        my_logger.info(f"actions NotFound: {action_name}")
        raise Exception(f"actions NotFound: {action_name}")
    _actions(config)
    my_logger.info(f"actions Done: {action_name}")


def esc_once():
    pydirectinput.press("esc")
    time.sleep(1)


# d2_operation.active_window()
# time.sleep(2)
# do_actions("轨道开启PM第一次")
# # do_actions("PM占点")
