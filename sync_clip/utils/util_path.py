import os
from typing import *


if TYPE_CHECKING:
    pass

HOME_PATH = os.path.expanduser('~')

PROJECT_NAME = "sync_clip"


def ensure_dir_exist(dir_path):
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    return dir_path


PROJECT_CACHE_PATH = ensure_dir_exist(
    os.path.join(HOME_PATH, f".{PROJECT_NAME}"))
ensure_dir_exist(PROJECT_CACHE_PATH)


def judge_not_exist_isfile(path):
    return "." in path[-10:]


def join_ensure_exist(*paths):
    paths = [str(p) for p in paths]
    _path = os.path.join(*paths)
    if judge_not_exist_isfile(_path):
        ensure_dir_exist(os.path.dirname(_path))
    else:
        ensure_dir_exist(_path)
    return _path


def get_endpoint_index(filepath):
    return filepath.rindex(".")


def get_dir_file_extension_name(filepath):
    dir_name = os.path.dirname(filepath)
    base_filename = os.path.basename(filepath)
    endpoint_index = get_endpoint_index(base_filename)
    return (dir_name, base_filename[:endpoint_index],
            base_filename[endpoint_index + 1:])


def get_basename_without_extension(filepath):
    return get_dir_file_extension_name(filepath)[1]


def get_extensions(filepath):
    return get_dir_file_extension_name(filepath)[2]


def get_filepath_no_ext(filepath):
    endpoint_index = get_endpoint_index(filepath)
    return filepath[:endpoint_index]


def raise_error_if_not_exists(filepaths):
    for filepath in filepaths:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Missing filepath: {filepath}")
    return True


def get_cache_data_dir(folder: str):
    return (join_ensure_exist(PROJECT_CACHE_PATH, folder) if folder
            else PROJECT_CACHE_PATH)


def get_cache_data_filepath(folder: str = "", filename: str = ""):
    if not filename:
        raise ValueError("filename is not allow to be empty !!!")
    return join_ensure_exist(get_cache_data_dir(folder), filename)


def get_log_path(_file_, log_folder="script_logs"):
    folder_path = get_cache_data_dir(log_folder)
    file = os.path.basename(_file_)
    log_filename = f"{file[:file.rindex('.')]}.log"
    return os.path.join(folder_path, log_filename)
