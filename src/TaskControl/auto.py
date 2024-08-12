import asyncio
import time
from queue import Queue
from TaskControl.Base.BaseTask import Task, Event
from TaskControl.Base.TimerManager import TimerManager
from TaskControl.Base.CommonLogger import my_logger
from my_window.MainWindow import log_window
from TaskControl.ActControl import do_actions
from TaskControl.auto_OrbsofPower_mission.auto_orbsofpower_missionTask import AutoPowerMissionTask
from TaskControl.gen_leave.gen_leave import GenLeaveTask
from TaskControl.auto_OrbsofPower_mission.simple_mission_task import SimpleMissionTask

from TaskControl.auto_OrbsofPower_mission.get_leaves_num import get_leaves_item_quantity
from TaskControl.auto_OrbsofPower_mission.get_bounty_mission import get_mission
from settings import other_settings, mode
from utils import path_helper, d2_operation


pm_round = other_settings.rounds


class AutoBridge(object):
    def __init__(self):
        super().__init__()
        self.auto_leave_task = GenLeaveTask(finish_Callback=self.on_auto_leave_finish)
        self.use_leave_task = AutoPowerMissionTask(finish_Callback=self.on_use_leave_finish)
        self.simple_mission_task = SimpleMissionTask()
        self.event_queue = Queue()

    def init_task(self, task_class, event_handler=None):
        task = task_class(self.event_queue)
        if event_handler:
            task.register_event(event_handler)
        return task

    def start(self):
        self.event_queue.put((self.real_start, None))

        try:
            asyncio.run(self.check_queue())
        except KeyboardInterrupt:
            raise Exception
        except Exception as e:
            import traceback

            with open(path_helper.get_log("error.log"), "a", encoding="utf-8") as f:
                f.write(traceback.format_exc() + "\n")
                f.write(f"{e}\n")
            raise Exception

    def real_start(self, _):
        if mode.current_mod == 1:
            self.all_auto_mode()
        elif mode.current_mod == 2:
            self.simple_mode()
        elif mode.current_mod == 3:
            self.simple_get_leave()
        else:
            self.test_mode()

    def simple_mode(self):
        self.simple_mission_task.start(None)

    def simple_get_leave(self):
        self.auto_leave_task.start(200)

    def test_mode(self):
        self.log(f"执行测试模式", emit=True)
        self.log(f"开始行为 {mode.test_act}", emit=True)
        test_act = mode.test_act
        do_actions(test_act)
        self.log(f"测试结束", emit=True)

    def all_auto_mode(self):
        current_leave = get_leaves_item_quantity()
        self.log(f"检测到银叶数量 {current_leave}", emit=True)
        if current_leave > 100:
            self.use_leave_task.start(current_leave)
        else:
            self.auto_leave_task.start(pm_round)

    async def check_queue(self):
        # 让主函数一直循环
        while True:
            while not self.event_queue.empty():
                result = self.event_queue.get_nowait()
                func, event = result
                self.log(f"check_queue on_event={func.__name__}")
                func(event)
            await asyncio.sleep(1 / 30)

    def on_auto_leave_finish(self):
        self.use_leave_task.start(None)

    def on_use_leave_finish(self):
        self.auto_leave_task.start(pm_round)

    def stop(self):
        self.use_leave_task.stop_all_checks()
        self.auto_leave_task.stop_all_checks()

    def log(self, msg, emit=False):
        my_logger.info(msg)
        if emit:
            log_window.emit_log(msg)
