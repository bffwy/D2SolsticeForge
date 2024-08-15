import json
import os
from utils import path_helper
from settings import mode


class Event:
    def __init__(self, queue):
        self.queue = queue
        self.data = {}
        self.listeners = []

    def add_listener(self, listener):
        self.listeners.append(listener)

    def trigger(self):
        for listener in self.listeners:
            if callable(listener):
                self.queue.put((listener, self))
                # listener(self)


class Task:
    def __init__(self, queue):
        self.event = Event(queue)
        self.init()
        self.finish_check = False

    def init(self):
        file_path = path_helper.get_config(mode.task_config)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            task_config = config.get(self.__class__.__name__)
            if task_config:
                for key, value in task_config.items():
                    setattr(self, key, value)

    def start(self):
        raise NotImplementedError

    def register_event(self, func):
        self.event.add_listener(func)

    def event_time_out(self):
        if self.finish_check:
            return
        # self.event.data["time_out"] = 1
        self.event.trigger()
