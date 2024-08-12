from TaskControl.Base.CheckTaskBase import CheckTaskBase
from TaskControl.Base.TimerManager import TimerManager
from TaskControl.Base.CommonLogger import my_logger
from screenshot import get_similarity


class CheckFinishPM(CheckTaskBase):

    check_similarity = 0.8
    check_interval = 1
    check_time_out = 120

    def start_check(self):
        self.stop_check()
        self.finish_check = False
        self.timer_id = TimerManager.add_timer(self.round_time, self.real_start)

    def real_start(self):
        self.check()
        self.timeout_timer_id = TimerManager.add_timer(self.check_time_out, self.event_time_out)

    def check(self):
        if self.finish_check:
            return
        mask_ratio = get_similarity(self.check_image, self.check_box, self.debug)
        if mask_ratio >= self.check_similarity:
            self.event.data = {"check": True}
            self.trigger()
            return
        self.timer_id = TimerManager.add_timer(self.check_interval, self.check)
