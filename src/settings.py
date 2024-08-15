import tomllib
import dataclasses
from pathlib import Path
from utils import path_helper

config_path = path_helper.get_config("settings.toml")

SETTINGS_PATH = Path(config_path)


@dataclasses.dataclass
class mission:
    next_page_button_pos: tuple[int]
    refresh_time: int
    refresh_pos_x: int
    refresh_pos_y: tuple[int]
    x_range: tuple[int]
    min_radius: int
    max_radius: int
    y_diff: int
    perfect_like: int
    get_white_mission: bool


@dataclasses.dataclass
class other:
    use_dim: bool
    rounds: int
    skill_rounds: int
    start_use_leave: int
    leave_leaf: int


@dataclasses.dataclass
class leave_detect:
    act_to_leave_page: str
    leave_right_down_pos: tuple[int]
    check_box: tuple[int]
    back_to_pre_page_act: str
    debug: bool


@dataclasses.dataclass
class mode:
    current_mod: int
    test_act: str
    task_config: str
    is_1280_resolution: bool


settings = tomllib.loads(SETTINGS_PATH.read_text("utf-8"))
mission_settings = mission(**settings.pop("mission"))
other_settings = other(**settings.pop(f"other"))
mode = mode(**settings.pop("mode"))
leave_detect = leave_detect(**settings.pop("leave_detect"))
