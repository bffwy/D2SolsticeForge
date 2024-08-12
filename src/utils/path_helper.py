import os


def get_real_path(relative_path, dir_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(current_dir, "..", "..", dir_name)
    file_path = os.path.join(target_dir, relative_path)
    real_path = os.path.abspath(file_path)
    if not os.path.exists(real_path):
        print(f"miss file : {real_path}")
        # with open(get_log("error.log"), "a", encoding="utf-8") as f:
        #     f.write(f"miss file : {real_path}" + "\n")
    return real_path


def get_config(file_path):
    return get_real_path(file_path, "config")


def get_asset(file_path):
    return get_real_path(file_path, "asset")


def get_resource(file_path):
    return get_real_path(file_path, "resource")


def get_log(file_path):
    path = get_real_path(file_path, "logs")
    if not os.path.exists(path):
        # 创建文件 和 文件夹
        print(f"dir path : {os.path.dirname(path)}")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            pass
    return path
