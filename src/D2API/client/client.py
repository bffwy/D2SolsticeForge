import sys
import os

parent_dir_name = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir_name)
sys.path.append(os.path.dirname(parent_dir_name))

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QInputDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from utils import path_helper


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super(SystemTrayIcon, self).__init__(parent)
        # icon_path = path_helper.get_resource("my_window/running.svg")
        icon_path = path_helper.get_resource("my_window/unverified1.svg")

        self.setIcon(QIcon(icon_path))  # 设置图标
        self.activated.connect(self.click_tray)
        # 创建菜单
        self.menu = QMenu()
        # 创建认证按钮
        self.auth_action = QAction("认证", self)
        self.menu.addAction(self.auth_action)
        self.auth_action.triggered.connect(self.open_auth_url)

        # 创建模式按钮和子菜单
        self.mode_menu = QMenu()
        self.mode_menu.setTitle("模式")
        self.mode1_action = QAction("模式1", self)
        self.mode1_action.setCheckable(True)  # 设置为可勾选
        self.mode1_action.setChecked(False)  # 设置初始状态为未勾选
        self.mode2_action = QAction("模式2", self)
        self.mode2_action.setCheckable(True)  # 设置为可勾选
        self.mode2_action.setChecked(False)  # 设置初始状态为未勾选

        self.mode_menu.addAction(self.mode1_action)
        self.mode_menu.addAction(self.mode2_action)
        self.menu.addMenu(self.mode_menu)

        # 创建间隔按钮
        self.interval_action = QAction("间隔", self)
        self.interval_action.triggered.connect(self.set_interval)
        self.menu.addAction(self.interval_action)

        # 创建退出按钮
        self.quit_action = QAction("退出", self)
        self.quit_action.triggered.connect(app.quit)
        self.menu.addAction(self.quit_action)

        self.setContextMenu(self.menu)

    def click_tray(self, reason):
        if reason == 3:  # 单击
            self.showMessage("提示", "单击了托盘图标")
            icon_path = path_helper.get_resource("my_window/running.svg")
            self.setIcon(QIcon(icon_path))  # 设置图标

    def set_interval(self):
        try:
            interval, ok = QInputDialog.getInt(None, "设置间隔", "请输入间隔（分钟）", min=1)
            if ok:
                self.interval_action.setText(f"间隔（当前：{interval}分钟）")
            else:
                self.showMessage("提示", "取消")
        except Exception as e:
            print(f"An error occurred: {e}")

    def open_auth_url(self):
        QDesktopServices.openUrl(QUrl("http://www.example.com"))
        icon_path = path_helper.get_resource("my_window/stop.svg")
        self.setIcon(QIcon(icon_path))  # 设置图标

    def check_modes(self):
        if self.mode1_action.isChecked():
            print("模式1被勾选")
        if self.mode2_action.isChecked():
            print("模式2被勾选")


if __name__ == "__main__":
    import sys

    def handle_exception(exc_type, exc_value, exc_traceback):
        print("Uncaught exception:", exc_type, exc_value)

    sys.excepthook = handle_exception

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray = SystemTrayIcon()
    tray.show()
    sys.exit(app.exec_())

# https://www.bungie.net/zh-chs/Application/Detail/52649
# /Platform/User/GetMembershipsForCurrentUser/
# https://www.bungie.net/Platform/Destiny2/254/Profile/30287387/LinkedProfiles/?getAllMemberships=tru
