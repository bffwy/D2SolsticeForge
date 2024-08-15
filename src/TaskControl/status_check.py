import time
from screenshot import get_similarity
from TaskControl.Base.TimerManager import ClassTimerManager
from TaskControl.Base.CommonLogger import my_logger
from TaskControl.ActControl import do_actions, esc_once

interval = 60

check_image = {"leave_status": [442, 321, 627, 376], "in_orbit_1280": [50, 724, 106, 748]}


class StatusControl(object):
    def __init__(self, finish_Callback=None):
        self.finish_callback = finish_Callback
        self.timer = ClassTimerManager()

    def start(self):
        self.timer.add_timer(interval, self.real_check)

    def real_check(self):
        ret = get_similarity("leave_status", check_image["leave_status"], debug=False)
        if ret >= 0.8:
            my_logger.info("检测到玩家离开")
            self.trigger()
            return
        self.timer.add_timer(interval, self.real_check)

    def trigger(self):
        if self.finish_callback:
            self.finish_callback()

    def get_back_to_orbit(self):
        esc_once()
        time.sleep(3)
        ret = get_similarity("in_orbit_1280", check_image["in_orbit_1280"], debug=False)
        if ret >= 0.8:
            my_logger.info("检测到玩家回到轨道")
