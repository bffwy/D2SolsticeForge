import asyncio
import time
from queue import Queue
from D2API.api import move_items_from_postmaster_to_vault

from TaskControl.Base.BaseTask import Task, Event
from TaskControl.Base.TimerManager import TimerManager
from TaskControl.Base.CommonLogger import my_logger
from my_window.MainWindow import log_window
from TaskControl.ActControl import do_actions
from TaskControl.auto_OrbsofPower_mission.CheckTask.CheckMissionFinishTask import CheckMissionFinishTask
from TaskControl.auto_OrbsofPower_mission.CheckTask.CheckRebornTask import CheckRebornTask
from TaskControl.auto_OrbsofPower_mission.CheckTask.PlayerDieCheckTask import PlayerDieCheckTask
from TaskControl.auto_OrbsofPower_mission.CheckTask.EnterLWTask import EnterLWTask
from TaskControl.auto_OrbsofPower_mission.get_bounty_mission import get_mission
from TaskControl.auto_OrbsofPower_mission.get_leaves_num import get_leaves_item_quantity
from TaskControl.CheckTask.CheckBackToOrbit import CheckBackToOrbit

from settings import other_settings


class Data:
    def __init__(self):
        self.round = 0
        self.round_time = []
        self.round_start_time = None

    def add_small_round(self):
        if not self.round_start_time:
            return
        use_time = time.time() - self.round_start_time
        self.round_start_time = None
        self.round += 1
        self.round_time.append(use_time)

    def get_average_time(self):
        round_average = (
            self._seconds_to_mm_ss(sum(self.round_time) / len(self.round_time)) if self.round_time else "00:00"
        )
        return round_average

    def _seconds_to_mm_ss(self, seconds):
        return "{:02d}:{:02d}".format(int(seconds) // 60, int(seconds) % 60)

    def re_init(self):
        self.round = 0
        self.round_start_time = None


class SimpleMissionTask(object):
    def __init__(self, finish_Callback=None):
        self.finish_callback = finish_Callback
        self.event_queue = Queue()
        self.init_tasks()
        self.main_task = None
        self.goal_finish = False
        self.finish_mission = False
        self.current_leave = 0
        self.data = Data()

    def init_tasks(self):
        self.check_mission_finish = self.init_task(CheckMissionFinishTask, self.on_mission_finish)
        self.check_mission_finish.check_time_out = 999999

    def init_task(self, task_class, event_handler=None):
        task = task_class(self.event_queue)
        if event_handler:
            task.register_event(event_handler)
        return task

    def start(self, current_leave=None):
        self.log(f"开始刷能量球", emit=True)
        get_mission()
        if current_leave:
            self.current_leave = current_leave
        else:
            self.current_leave = get_leaves_item_quantity()

        self.event_queue.put((self.start_task, None))
        try:
            loop = asyncio.get_running_loop()  # 获取当前运行的事件循环
            loop.create_task(self.check_queue())  # 在当前事件循环中创建一个新的任务
        except KeyboardInterrupt:
            raise Exception
        except Exception as e:
            raise Exception

    async def check_queue(self):
        while True:
            while not self.event_queue.empty():
                result = self.event_queue.get_nowait()
                func, event = result
                self.log(f"check_queue on_event={func.__name__}")
                func(event)
            await asyncio.sleep(1 / 30)
            if self.goal_finish:
                break

    def start_task(self, _):
        self.data.add_small_round()
        if self.finish_mission:
            self.handle_mission_completion()
        self.update_main_task()

    def handle_mission_completion(self):
        self.finish_mission = False
        self.claim_reward()
        self.get_new_mission()
        if other_settings.use_dim:
            move_items_from_postmaster_to_vault()

    def claim_reward(self):
        do_actions("领取悬赏")
        time.sleep(1)
        self.log("领取新悬赏", emit=True)

    def get_new_mission(self):
        use_leave = get_mission()
        self.current_leave -= use_leave
        if self.current_leave < 0:
            self.goal_finish = True

    def update_main_task(self):
        if self.main_task and not self.main_task.done():
            self.main_task.cancel()
        self.main_task = asyncio.create_task(self.main())

    async def main(self):
        small_avg = self.data.get_average_time()
        self.log(f"开始第 {self.data.round + 1} 轮, 平均耗时 {small_avg}", emit=True)
        self.log(f"当前银叶 {self.current_leave}", emit=True)
        self.data.small_round_start_time = time.time()
        await asyncio.sleep(0.5)
        self.check_mission_finish.start()
        times = 999999
        while times > 0:
            times -= 1
            do_actions("kf技能循环")
            await asyncio.sleep(5)

    def on_mission_finish(self, event: Event):
        data = event.data
        if data.get("check"):
            self.log("检测到悬赏完成", emit=True)
            self.finish_mission = True
        self.clear_timer_and_restart()

    def cancel_main(self):
        if self.main_task and not self.main_task.done():
            self.main_task.cancel()
            self.main_task = None

    def stop_all_checks(self, is_die=False):
        # 清空消息队列
        self.log(f"stop_all_checks")
        self.cancel_main()
        self.event_queue.queue.clear()
        # TimerManager.clear_timers()

    def clear_timer_and_restart(self):
        self.log(f"clear_timer_and_restart")
        self.stop_all_checks()
        self.event_queue.put((self.start_task, None))

    def log(self, msg, emit=False):
        my_logger.info(msg)
        if emit:
            log_window.emit_log(msg)
