import os
import xml.etree.ElementTree as ET
import pydirectinput
import win32gui
import win32con

keys_we_press = [
    "hold_zoom",
    "primary_weapon",
    "special_weapon",
    "heavy_weapon",
    "move_forward",
    "move_backward",
    "move_left",
    "move_right",
    "jump",
    "toggle_sprint",
    "interact",
    "melee_uncharged",
    "ui_open_director",
    "ui_abort_activity",
    "ui_open_start_menu_settings_tab",
    "ui_open_director_pursuits_tab",
]

# 定义转换表
map_key = {
    "shift": "shiftleft",
    "control": "ctrlleft",
    "alt": "altleft",
    "keypad/": "divide",
    "keypad*": "multiply",
    "keypad-": "subtract",
    "keypad+": "add",
    "keypadenter": "keypadenter",
    "leftmousebutton": "primary",
    "middlemousebutton": "middle",
    "rightmousebutton": "secondary",
    # "extramousebutton1": "XButton1",
    # "extramousebutton2": "XButton2",
    "mousewheelup": "WheelUp",
    "mousewheeldown": "WheelDown",
}

key_chinese_2_en = {
    "向前移动": "move_forward",
    "向后移动": "move_backward",
    "向左移动": "move_left",
    "向右移动": "move_right",
    "终结技": "highlight_player",
    "动作1": "emote_1",
    "动作2": "emote_2",
    "动作3": "emote_3",
    "动作4": "emote_4",
    "返回轨道": "ui_abort_activity",
    "射击": "fire",
    "填装": "reload",
    "自动近战": "melee",
    "充能近战": "melee_charged",
    "未充能近战": "melee_uncharged",
    "按住冲刺": "hold_sprint",
    "切换冲刺": "toggle_sprint",
    "按住蹲伏": "hold_crouch",
    "切换蹲伏": "toggle_crouch",
    "职业技能": "class_ability",
    "空中移动": "air_move",
    "互动": "interact",
    "手雷": "grenade",
    "超能": "super",
    "超凡": "utility_ability",
    "部署机灵": "ui_gamepad_button_back",
    "打开导航器": "ui_open_director",
    "打开任务": "ui_open_director_pursuits_tab",
    "打开设置": "ui_open_start_menu_settings_tab",
    "打开名单": "ui_open_director_roster_tab",
    "打开物品栏": "ui_open_start_menu_inventory_tab",
    "按住放大": "hold_zoom",
    "切换到动能武器": "primary_weapon",
    "切换到能量武器": "special_weapon",
    "切换到威能武器": "heavy_weapon",
    "跳跃": "jump",
}

key_en_2_chinese = {v: k for k, v in key_chinese_2_en.items()}


def get_d2_keybinds(k):
    # 读取文件
    try:
        tree = ET.parse(os.path.join(os.getenv("APPDATA"), "Bungie", "DestinyPC", "prefs", "cvars.xml"))
        root = tree.getroot()
    except FileNotFoundError:
        return False

    # 解析键绑定
    b = {}
    for n in k:
        cvar = root.find(f'.//cvar[@name="{n}"]')
        if cvar is not None:
            value = (
                cvar.get("value").split("!")[0]
                if "unused" not in cvar.get("value").split("!")[0]
                else cvar.get("value").split("!")[1]
            )
            value = value.replace(" ", "")
            b[n] = map_key[value] if value in map_key else value
        else:
            b[n] = "unused"

    return b


real_use_key = {
    "打开任务",
    "向前移动",
    "向后移动",
    "返回轨道",
    "切换冲刺",
    "切换到威能武器",
    "未充能近战",
    "打开导航器",
    "部署机灵",
    "打开物品栏",
}

bind_key_en = get_d2_keybinds([key_chinese_2_en[key] for key in real_use_key])
bind_key_chn = {key_en_2_chinese[k]: v for k, v in bind_key_en.items()}

mouse_buttons = ["primary", "secondary", "middle", "XButton1", "XButton2"]

for key, value in bind_key_en.items():
    if not value:
        raise Exception(f"需要绑定键: {key_en_2_chinese[key]}")


def key_down(bind_name, click=False):
    key = bind_key_en[bind_name]
    if key in mouse_buttons:
        if click:
            pydirectinput.mouseDown(button=key)
        else:
            pydirectinput.keyDown(key)
    elif key in ["WheelUp", "WheelDown"]:
        pydirectinput.scroll(1 if key == "WheelUp" else -1)
    else:
        if click:
            pydirectinput.press(key)
        else:
            pydirectinput.keyDown(key)


def key_up(bind_name):
    key = bind_key_en[bind_name]
    if key in mouse_buttons:
        pydirectinput.mouseUp(button=key)
    else:
        pydirectinput.keyUp(key)


def key_down_chn(bind_name, click=False):
    key = bind_key_chn[bind_name]
    if key in mouse_buttons:
        if click:
            pydirectinput.mouseDown(button=key)
        else:
            pydirectinput.keyDown(key)
    elif key in ["WheelUp", "WheelDown"]:

        pydirectinput.scroll(1 if key == "WheelUp" else -1)
    else:
        if click:
            pydirectinput.press(key)
        else:
            pydirectinput.keyDown(key)


def key_up_chn(bind_name):
    key = bind_key_chn[bind_name]
    if key in mouse_buttons:
        pydirectinput.mouseUp(button=key)
    else:
        pydirectinput.keyUp(key)


def free_all():
    for opt, key in bind_key_en.items():
        if key in mouse_buttons:
            pydirectinput.mouseUp(button=key)
        else:
            pydirectinput.keyUp(key)


window_x = None
window_y = None


def active_window(match_string="Destiny 2"):
    global window_x, window_y

    def enum_windows():
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                windows.append((hwnd, win32gui.GetWindowText(hwnd)))

        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows

    windows = enum_windows()

    for hwnd, title in windows:
        if match_string in title and ("Tiger D3D Window" == win32gui.GetClassName(hwnd)):
            win32gui.ShowWindow(hwnd, 5)
            win32gui.SetForegroundWindow(hwnd)
            # win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
            win32gui.BringWindowToTop(hwnd)
            ret = win32gui.GetWindowRect(hwnd)
            window_x = ret[0]
            window_y = ret[1]
            break


def init_window():
    global window_x, window_y

    def enum_windows():
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                windows.append((hwnd, win32gui.GetWindowText(hwnd)))

        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows

    windows = enum_windows()

    for hwnd, title in windows:
        if "Destiny 2" in title and ("Tiger D3D Window" == win32gui.GetClassName(hwnd)):
            ret = win32gui.GetWindowRect(hwnd)
            print("pos", ret)
            window_x = ret[0]
            window_y = ret[1]
            break


def get_d2_pos(x, y):
    global window_x, window_y
    if window_x is None:
        init_window()
    return window_x + x, window_y + y


def get_d2_position(pos):
    global window_x, window_y
    if window_x is None:
        init_window()
    x, y = pos
    return window_x + x, window_y + y


def get_d2_box(box):
    x, y, x1, y1 = box
    x, y = get_d2_pos(x, y)
    x1, y1 = get_d2_pos(x1, y1)
    return x, y, x1, y1


def back_2_d2_pos(x, y):
    global window_x, window_y
    if window_x is None:
        init_window()
    return x - window_x, y - window_y


def d2_move(x, y):
    x, y = get_d2_pos(x, y)
    pydirectinput.moveTo(x, y)


# print(back_2_d2_pos(1486, 902))
# print(back_2_d2_pos(1536, 931))

# d2 pos (109, 53, 2045, 1172)
# 876, 335
