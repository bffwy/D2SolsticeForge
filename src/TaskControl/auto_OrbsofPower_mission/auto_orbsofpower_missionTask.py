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
        self.small_rounds = 0
        self.big_rounds = 0
        self.small_round_time = []
        self.big_round_time = []
        self.small_round_start_time = None

    def add_small_round(self, finish_big_rounds=False):
        if not self.small_round_start_time:
            return
        use_time = time.time() - self.small_round_start_time
        self.small_round_start_time = None

        self.small_rounds += 1
        self.small_round_time.append(use_time)
        if finish_big_rounds:
            self.big_rounds += 1
            self.big_round_time.append(sum(self.small_round_time))
            self.small_rounds = 0
            self.small_round_time = []

    def get_average_time(self):
        small_round_average = (
            self._seconds_to_mm_ss(sum(self.small_round_time) / len(self.small_round_time))
            if self.small_round_time
            else "00:00"
        )
        big_round_average = (
            self._seconds_to_mm_ss(sum(self.big_round_time) / len(self.big_round_time))
            if self.big_round_time
            else "00:00"
        )
        return small_round_average, big_round_average

    def get_current_rounds(self):
        return self.small_rounds, self.big_rounds

    def _seconds_to_mm_ss(self, seconds):
        return "{:02d}:{:02d}".format(int(seconds) // 60, int(seconds) % 60)


class AutoPowerMissionTask(object):
    def __init__(self, finish_Callback=None):
        self.finish_callback = finish_Callback
        self.event_queue = Queue()
        self.init_tasks()
        self.main_task = None
        self.goal_finish = False
        self.finish_mission = False
        self.current_leave = 0
        self.in_map = False
        self.end_mission = False
        self.data = Data()

    def init_tasks(self):
        self.check_tasks = []
        self.check_player_die_check = self.init_task(PlayerDieCheckTask, self.on_player_die)
        self.check_reborn_task = self.init_task(CheckRebornTask, self.on_player_reborn)
        self.check_mission_finish = self.init_task(CheckMissionFinishTask, self.on_mission_finish)
        self.enter_lw_task = self.init_task(EnterLWTask, self.on_enter_map)
        self.check_back_to_orbit = self.init_task(CheckBackToOrbit, self.on_back_to_orbit)

    def init_task(self, task_class, event_handler=None):
        task = task_class(self.event_queue)
        if event_handler:
            task.register_event(event_handler)
        self.check_tasks.append(task)
        return task

    def start(self, current_leave):
        self.log(f"开始刷能量球", emit=True)
        self.goal_finish = False
        self.in_map = False
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

        self.stop_all_checks()
        TimerManager.clear_timers()
        do_actions("遗愿回轨道")
        self.end_mission = False
        self.check_back_to_orbit.start()
        await self.final_check()

    async def final_check(self):
        while True:
            while not self.event_queue.empty():
                result = self.event_queue.get_nowait()
                func, event = result
                self.log(f"check_queue on_event={func.__name__}")
                func(event)
            await asyncio.sleep(1 / 30)
            if self.end_mission:
                break
        if self.finish_callback:
            self.finish_callback()

    def on_back_to_orbit(self, event: Event):
        self.log(f"检查回轨道完成", emit=True)
        self.end_mission = True

    def start_task(self, _):
        if self.in_map:
            self.data.add_small_round(finish_big_rounds=self.finish_mission)
            if self.finish_mission:
                self.handle_mission_completion()
            self.update_main_task()
        else:
            self.enter_lw_task.start()

    def on_enter_map(self, event: Event):
        self.in_map = True
        self.log(f"进图完成", emit=True)
        self.event_queue.put((self.start_task, None))

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
        req = min(other_settings.leave_leaf, 0)
        if self.current_leave <= req:
            self.goal_finish = True

    def update_main_task(self):
        if self.main_task and not self.main_task.done():
            self.main_task.cancel()
        self.main_task = asyncio.create_task(self.main())

    async def main(self):
        small, big = self.data.get_current_rounds()
        small_avg, big_avg = self.data.get_average_time()
        self.log(f"开始第 {big+1} 大轮, 平均耗时 {big_avg}", emit=True)
        self.log(f"开始第 {small+1} 小轮, 平均耗时 {small_avg}", emit=True)
        self.log(f"当前银叶 {self.current_leave}", emit=True)
        self.data.small_round_start_time = time.time()
        await asyncio.sleep(0.5)

        do_actions("走到固定位置")
        times = other_settings.skill_rounds
        self.check_mission_finish.start()
        self.check_player_die_check.start()
        while times > 0:
            times -= 1
            do_actions("技能循环")
            await asyncio.sleep(0.1)
        do_actions("3号位武器自杀")

    def on_player_die(self, event: Event):
        self.log(f"检测玩家死亡", emit=True)
        self.stop_all_checks(is_die=True)
        self.start_check_player_reborn()

    def start_check_player_reborn(self):
        self.log(f"等待玩家重生", emit=True)
        self.stop_all_checks()
        time.sleep(2)
        self.check_reborn_task.start()

    def on_player_reborn(self, event):
        self.log(f"检测玩家复活", emit=True)
        self.clear_timer_and_restart()
        # # 测试用
        # self.goal_finish = True

    def on_mission_finish(self, event: Event):
        data = event.data
        if data.get("check"):
            self.log("检测到悬赏完成", emit=True)
            self.finish_mission = True
            do_actions("3号位武器自杀")

    def cancel_main(self):
        if self.main_task and not self.main_task.done():
            self.main_task.cancel()
            self.main_task = None

    def stop_all_checks(self, is_die=False):
        # 清空消息队列
        self.log(f"stop_all_checks")
        for task in self.check_tasks:
            if isinstance(task, CheckMissionFinishTask) and is_die:
                continue
            task.stop_check()
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
