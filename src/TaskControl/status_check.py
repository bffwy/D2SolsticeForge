import time
from screenshot import get_similarity
from TaskControl.Base.TimerManager import ClassTimerManager
from TaskControl.Base.CommonLogger import my_logger
from TaskControl.ActControl import do_actions, esc_once, enter


check_image = {
    "in_orbit": [50, 724, 106, 748],
    "error_page": [343, 312, 422, 390],
    "leave_page": [339, 329, 423, 413],
    "first_page": [400, 332, 903, 476],
    "login_page": [50, 720, 147, 747],
}


def start_check_in_orbit(func):
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.check_in_orbit = True
        self.adjust_tick_interval()
        if callable(self.error_callback):
            self.do_error_callback()
        return result

    return wrapper


class StatusControl(object):

    def __init__(self, error_callback=None, finish_Callback=None):
        self.error_callback = error_callback
        self.finish_callback = finish_Callback
        self.timer = ClassTimerManager()
        self.timer_id = None
        self.check_in_orbit = False
        self.interval = 15

        # 定义一个字典来存储每种状态的处理函数
        self.status_handlers = {
            "error_page": self.handle_error_page,
            "leave_page": self.handle_leave_status,
            "first_page": self.handle_first_page,
            "login_page": self.handle_login,
            "in_orbit": self.handle_in_orbit,
        }

    def adjust_tick_interval(self):
        if self.check_in_orbit:
            # 加速
            self.interval = 3
        else:
            self.interval = 15

    @start_check_in_orbit
    def handle_error_page(self):
        my_logger.info("检测到错误界面")
        esc_once()

    @start_check_in_orbit
    def handle_leave_status(self):
        my_logger.info("检测到玩家离开状态")
        esc_once()

    @start_check_in_orbit
    def handle_first_page(self):
        my_logger.info("检测到在起始登录界面")
        enter()

    @start_check_in_orbit
    def handle_login(self):
        my_logger.info("检测到玩家在登录界面")
        do_actions("选角色")

    def handle_in_orbit(self):
        if self.check_in_orbit:
            my_logger.info("检测到玩家在轨道")
            self.check_in_orbit = False
            self.adjust_tick_interval()
            if callable(self.finish_callback):
                self.finish_callback()

    def do_error_callback(self):
        if callable(self.error_callback):
            self.error_callback()

    def start(self):
        if self.timer_id:
            self.timer.cancel_timer(self.timer_id)
        self.timer_id = self.timer.add_timer(self.interval, self.real_check)

    def real_check(self):
        for status, handler in self.status_handlers.items():
            if status in check_image:
                ret = get_similarity(f"status/{status}", check_image[status], debug=False)
                if ret >= 0.8:
                    handler()  # 调用相应的处理函数
                    break

        self.timer_id = self.timer.add_timer(self.interval, self.real_check)
