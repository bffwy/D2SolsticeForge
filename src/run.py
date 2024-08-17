import multiprocessing

multiprocessing.freeze_support()
from TaskControl.auto import AutoBridge

from TaskControl.Base.CommonLogger import my_logger
from TaskControl.Base.TimerManager import TimerManager
from my_window.MainWindow import log_window
from utils import path_helper, d2_operation
from D2API.api import stop_thread


if __name__ == "__main__":
    my_logger.info("程序启动")
    d2_operation.active_window()
    new_task = AutoBridge()

    try:
        new_task.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        import traceback

        traceback.print_exc()
        with open(path_helper.get_log("error.log"), "a", encoding="utf-8") as f:
            f.write(traceback.format_exc() + "\n")
            f.write(f"{e}\n")

        d2_operation.active_window("Visual Studio Code")
        my_logger.critical(e)
        my_logger.info("程序已停止，请检查日志文件")
        # _ = input("按回车键退出...")
    finally:
        stop_thread()
        d2_operation.free_all()
        log_window.close_window()
        TimerManager.clear_timers()
        # new_task.stop_all_checks()
        new_task.stop()


# pipenv run pyinstaller --noconfirm --onedir --console --clean "D:/Work/git_work_space/d2-auto-work/src/run.py"
# pipenv run pyinstaller --noconfirm --onedir --console --debug "all" --clean "D:/Work/git_work_space/d2-auto-work/src/run.py"
# pipenv run pyinstaller .\run.spec --noconfir
