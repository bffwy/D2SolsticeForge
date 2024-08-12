from TaskControl.Base.CheckTaskBase import CheckTaskBase
from screenshot import get_similarity
from TaskControl.Base.TimerManager import TimerManager
from TaskControl.Base.CommonLogger import my_logger
from TaskControl.ActControl import do_actions


class EnterLWTask(CheckTaskBase):
    enter_map_time = 20
    check_time_out = 10
    check_similarity = 0.7
    check_interval = 1

    def __init__(self, queue):
        super().__init__(queue)
        self.check_timer_id = None

    def start(self):
        self.enter_map()

    def enter_map(self):
        do_actions("轨道进遗愿地图")
        self.timer_id = TimerManager.add_timer(self.enter_map_time, self.check_load_map)

    def check_load_map(self):
        self.timeout_timer_id = TimerManager.add_timer(self.check_time_out, self.event_time_out)
        self.real_check_load_map()

    def real_check_load_map(self):
        x = get_similarity(self.check_image, self.check_box, self.base_on_2560, self.debug)
        if x >= self.check_similarity:
            my_logger.info(f"real_check_load_map finish similarity={x}")
            self.trigger()
            return
        self.check_timer_id = TimerManager.add_timer(self.check_interval, self.real_check_load_map)
