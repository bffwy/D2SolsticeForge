# -*- coding: utf-8 -*-

import os
import sys

parent_dir_name = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir_name)
sys.path.append(os.path.dirname(parent_dir_name))

import json
import requests
import fnmatch
from pathlib import Path
from utils import path_helper
from utils.patterns import Singleton
from D2API import CONST, config


COMMON_HEADERS = {
    "X-API-Key": config.dim_settings.x_api_key,
    "Content-Type": "application/json",
}

BASE_URL = "https://www.bungie.net"

version_id = "227047.24.07.25.1730-3-bnet.56478"

component_path = {}
interact_language = ["zh-chs", "en"]


def store_data(data):
    jsonWorldComponentContentPaths = data["Response"]["jsonWorldComponentContentPaths"]
    for language, data_dict in jsonWorldComponentContentPaths.items():
        if language in interact_language:
            component_path[language] = data_dict


def init_component_path():
    folder = path_helper.get_resource("Doc")
    file_path = os.path.join(folder, f"manifest.json")
    load = False
    if os.path.exists(file_path):
        data = load_local_json(file_path)
        if data:
            load = True
            store_data(data)
    if not load:
        get_new_version()


def get_new_version():
    """获取 inventory 信息"""
    api_path = "/Platform/Destiny2/Manifest"
    r = requests.get(BASE_URL + api_path, headers=COMMON_HEADERS)
    if r.status_code == 200:
        try:
            data = r.json()
            folder = path_helper.get_resource("Doc")
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            store_data(data)
        except Exception as e:
            pass


max_threshold = 1 * 1024 * 1024  # 2MB

interest_Definition_data = [
    "DestinyInventoryItemLiteDefinition",
    "DestinySandboxPerkDefinition",
    "DestinyStatDefinition",
    "DestinyInventoryBucketDefinition",
    "DestinyEquipmentSlotDefinition",
]


def split_json(file_path, threshold):
    base_name = os.path.basename(file_path)
    file_name = os.path.splitext(base_name)[0]
    dir_name = file_name + "_dir"
    output_dir = os.path.join(os.path.dirname(file_path), dir_name)
    os.makedirs(output_dir, exist_ok=True)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    part = 1
    size = 0
    output = {}
    for key, value in data.items():
        output[key] = value
        size += len(json.dumps({key: value}))
        if size > threshold:
            save_file_path = os.path.join(output_dir, f"{file_name}_part{part}.json")
            with open(save_file_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False)
            part += 1
            size = 0
            output = {}
    if output:
        save_file_path = os.path.join(output_dir, f"{file_name}_part{part}.json")
        with open(save_file_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False)
    os.remove(file_path)


def read_json_parts(file_path):
    dir_path = Path(file_path)
    file_name = dir_path.stem.split("_")[0] + "*_part*.json"
    data = {}
    for entry in dir_path.iterdir():
        if entry.is_file() and fnmatch.fnmatch(entry.name, file_name):
            with open(entry, "r", encoding="utf-8") as f:
                data.update(json.load(f))
    return data


def load_local_json(file_path):
    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    elif os.path.isdir(file_path):
        data = read_json_parts(file_path)
    else:
        data = None
    return data


def get_json_data_from_net(key, url_path):
    folder = path_helper.get_resource("Doc")
    os.makedirs(folder, exist_ok=True)

    r = requests.get(BASE_URL + url_path)

    if r.status_code == 200:
        data = r.json()
        name = key
        file_type = url_path.split(".", -1)[-1]
        file_path = os.path.join(folder, f"{name}.{file_type}")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        file_size = os.path.getsize(file_path)
        if file_size > max_threshold:
            split_json(file_path, max_threshold)
        return data
    else:
        print("load_data_fail:", r)
        print(r.json())


def check_and_load_from_net(definition_key):
    # 检查文件是否下载，如果没有，就下载
    folder = path_helper.get_resource("Doc")
    file_path = os.path.join(folder, f"{definition_key}.json")
    file_dir_path = os.path.join(folder, f"{definition_key}_dir")

    if os.path.exists(file_path):
        return load_local_json(file_path)
    elif os.path.exists(file_dir_path):
        return read_json_parts(file_dir_path)
    else:

        data = get_json_data_from_net(definition_key, component_path["zh-chs"][definition_key])
    return data


def load_Data():
    folder = path_helper.get_resource("Doc")
    os.makedirs(folder, exist_ok=True)

    local_files = {}
    for item in os.scandir(folder):
        full_name = os.path.basename(item.path)
        file_name = os.path.splitext(full_name)[0]
        local_files[file_name] = item

    for key in interest_Definition_data:
        if key in local_files or f"{key}_dir" in local_files:
            load_local_json(item.path)
        else:
            for language in interact_language:
                if key in component_path[language]:
                    get_json_data_from_net(f"{key}_{language}", component_path[language][key])


class DestinyManifestData(Singleton):
    def __init__(self):
        self._data = {}

    def get(self, key):
        if key not in self._data:
            self._data[key] = check_and_load_from_net(f"{key}_zh-chs")
        return self._data[key]


def get_item_bucketTypeHash_by_hash(item_hash):
    find_key = "DestinyInventoryItemLiteDefinition"
    item_hash = str(item_hash)
    destiny_manifest_data = DestinyManifestData()
    item = destiny_manifest_data.get(find_key).get(item_hash, {})
    return item.get("inventory", {}).get("bucketTypeHash")


init_component_path()
# get_new_version()
# check_and_load_from_net("DestinyStatDefinition")
# print(get_item_bucketTypeHash_by_hash("1767106452"))
# load_Data()
# BucketTypeHash = get_item_bucketTypeHash_by_hash("3423574140")
# print(BucketTypeHash)
# print(type(BucketTypeHash))
