import asyncio
import time
from queue import Queue
from TaskControl.Base.BaseTask import Task, Event
from TaskControl.Base.TimerManager import TimerManager
from TaskControl.Base.CommonLogger import my_logger
from my_window.MainWindow import log_window
from TaskControl.ActControl import do_actions, esc_once
from TaskControl.gen_leave.CheckTask.CheckFinishPM import CheckFinishPM
from TaskControl.gen_leave.CheckTask.EnterPMTask import EnterPMTask
from TaskControl.CheckTask.CheckBackToOrbit import CheckBackToOrbit


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


class GenLeaveTask(object):

    def __init__(self, finish_Callback=None):
        self.finish_callback = finish_Callback
        self.event_queue = Queue()
        self.init_tasks()
        self.main_task = None
        self.goal_finish = False
        self.finish_mission = False
        self.current_leave = 0
        self.rounds = 0
        self.data = Data()

    def init_tasks(self):
        self.check_enter_map = self.init_task(EnterPMTask, self.on_enter_map)
        self.check_finish_task = self.init_task(CheckFinishPM, self.on_finish_pm)
        self.check_back_to_orbit = self.init_task(CheckBackToOrbit, self.on_back_to_orbit)

    def init_task(self, task_class, event_handler=None):
        task = task_class(self.event_queue)
        if event_handler:
            task.register_event(event_handler)
        return task

    def start(self, rounds):
        self.log(f"开始刷银叶 {rounds} 场", emit=True)
        self.goal_finish = False
        self.data.re_init()
        self.rounds = rounds

        self.event_queue.put((self.start_task, True))
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
        esc_once()
        self.log(f"结束PM刷银叶", emit=True)
        if self.finish_callback:
            self.finish_callback()

    def start_task(self, first_time=False):
        self.data.add_small_round()
        avg_time = self.data.get_average_time()
        self.log(f"开始第 {self.data.round + 1} 轮, 平均耗时 {avg_time}", emit=True)
        self.data.round_start_time = time.time()
        if not first_time:
            self.handle_round_completion()

        if self.goal_finish:
            return

        if not self.goal_finish:
            self.check_enter_map.start(first_time)

    def handle_round_completion(self):
        if self.data.round >= self.rounds:
            self.goal_finish = True

    def on_enter_map(self, event: Event):
        self.log(f"进图完成，开始占点", emit=True)
        if self.main_task and not self.main_task.done():
            self.main_task.cancel()
        self.main_task = asyncio.create_task(self.main())

    async def main(self):
        do_actions("PM占点")
        self.check_finish_task.start()

    def on_finish_pm(self, event: Event):
        self.log(f"检测到完成pm", emit=True)
        do_actions("PM完成回轨道")
        self.stop_all_checks()
        self.check_back_to_orbit.start()

    def on_back_to_orbit(self, event: Event):
        self.log(f"检测回到轨道，开启下一轮", emit=True)
        self.event_queue.put((self.start_task, False))

    def cancel_main(self):
        if self.main_task and not self.main_task.done():
            self.main_task.cancel()
            self.log(f"round end", emit=True)
            self.main_task = None

    def stop_all_checks(self):
        self.log(f"stop_all_checks")
        self.check_enter_map.stop_check()
        self.check_finish_task.stop_check()
        self.check_back_to_orbit.stop_check()
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
