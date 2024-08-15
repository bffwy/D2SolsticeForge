import threading
import uuid
from queue import Queue
from TaskControl.Base.CommonLogger import my_logger
from utils import path_helper

Global_Queue = Queue()


class TimerManager:
    timers = {}
    # lock = threading.Lock()
    lock = threading.RLock()  # Use RLock instead of Lock

    @classmethod
    def add_timer(cls, interval, func, args=(), repeat=False):
        timer_id = str(uuid.uuid4())
        timer = {"func": func, "args": args, "repeat": repeat, "interval": interval, "timer": None}
        with cls.lock:
            cls.timers[timer_id] = timer
        cls._start_timer(timer_id)
        return timer_id

    @classmethod
    def _start_timer(cls, timer_id):
        with cls.lock:
            timer = cls.timers[timer_id]
            timer["timer"] = threading.Timer(timer["interval"], cls._timer_callback, args=[timer_id])
            timer["timer"].daemon = True
            timer["timer"].start()

    @classmethod
    def _timer_callback(cls, timer_id):
        repeat = False
        with cls.lock:
            if timer_id not in cls.timers:
                return
            timer = cls.timers[timer_id]
            try:
                timer["func"](*timer["args"])
            except Exception as e:
                import traceback

                traceback.print_exc()
                with open(path_helper.get_log("error.log"), "a", encoding="utf-8") as f:
                    f.write(f"traceback at {timer['func'].__name__}" + "\n")
                    f.write(traceback.format_exc() + "\n")
                    f.write(f"{e}\n")
            repeat = timer["repeat"]
            if not repeat:
                if timer_id in cls.timers:
                    del cls.timers[timer_id]
        if repeat:
            cls._start_timer(timer_id)

    @classmethod
    def cancel_timer(cls, timer_id):
        with cls.lock:
            if timer_id and timer_id in cls.timers:
                timer = cls.timers[timer_id]
                timer["timer"].cancel()
                del cls.timers[timer_id]

    @classmethod
    def clear_timers(cls):
        with cls.lock:
            for timer_id in list(cls.timers.keys()):  # Use list() to create a copy of keys to avoid RuntimeError
                cls.cancel_timer(timer_id)


class ClassTimerManager:
    timers = {}
    lock = threading.RLock()  # Use RLock instead of Lock

    def add_timer(self, interval, func, args=(), repeat=False):
        timer_id = str(uuid.uuid4())
        timer = {"func": func, "args": args, "repeat": repeat, "interval": interval, "timer": None}
        with self.lock:
            self.timers[timer_id] = timer
        self._start_timer(timer_id)
        return timer_id

    def _start_timer(self, timer_id):
        with self.lock:
            timer = self.timers[timer_id]
            timer["timer"] = threading.Timer(timer["interval"], self._timer_callback, args=[timer_id])
            timer["timer"].daemon = True
            timer["timer"].start()

    def _timer_callback(self, timer_id):
        repeat = False
        with self.lock:
            if timer_id not in self.timers:
                return
            timer = self.timers[timer_id]
            try:
                timer["func"](*timer["args"])
            except Exception as e:
                import traceback

                traceback.print_exc()
                with open(path_helper.get_log("error.log"), "a", encoding="utf-8") as f:
                    f.write(f"traceback at {timer['func'].__name__}" + "\n")
                    f.write(traceback.format_exc() + "\n")
                    f.write(f"{e}\n")
            repeat = timer["repeat"]
            if not repeat:
                if timer_id in self.timers:
                    del self.timers[timer_id]
        if repeat:
            self._start_timer(timer_id)

    def cancel_timer(self, timer_id):
        with self.lock:
            if timer_id and timer_id in self.timers:
                timer = self.timers[timer_id]
                timer["timer"].cancel()
                del self.timers[timer_id]

    def clear_timers(self):
        with self.lock:
            for timer_id in list(self.timers.keys()):  # Use list() to create a copy of keys to avoid RuntimeError
                self.cancel_timer(timer_id)


# # Register clear_timers to be called on exit
# atexit.register(TimerManager.clear_timers)


# # 使用示例
# def my_func():
#     my_logger.info("Timer is up!")


# # 添加定时器
# timer_id = TimerManager.add_timer(5, my_func, repeat=True)
# my_logger.info(f"Timer ID: {timer_id}")

# 取消定时器
# TimerManager.cancel_timer(timer_id)
