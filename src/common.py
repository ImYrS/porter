"""
@Author: ImYrS Yang
@Date: 2023/2/12
@Copyright: ImYrS Yang
@Description:
"""

import hashlib
import random
import re
import string
import time
from typing import Optional


def formatted_time(
        time_stamp: Optional[int] = int(time.time()),
        secure_format: Optional[bool] = False,
) -> str:
    """
    时间戳转换为格式化时间

    :param time_stamp: 需要格式化的 Unix 时间戳
    :param secure_format: 是否需要安全的字符格式
    :return: 格式化后的时间
    """
    return (
        time.strftime("%Y%m%d_%H%M%S", time.localtime(time_stamp))
        if secure_format
        else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_stamp))
    )


def timestamp(ms: Optional[bool] = True) -> int:
    """
    获取当前时间戳

    :param ms: 是否以毫秒为单位
    :return: 时间戳
    """
    return int(time.time()) if not ms else int(time.time() * 1000)


now = timestamp


def rand_char(length=32, upper=False) -> str:
    """
    生成随机字符串

    :param length: 字符串长度
    :param upper: 是否为全大写
    :return:
    """
    # 数字 + 英文字母
    char = string.digits + string.ascii_letters
    if length > len(char):
        result = ""
        count = length
        while True:
            if count == 0:
                break

            if count > len(char):
                result += "".join(random.sample(char, len(char)))
                count -= len(char)
            else:
                result += "".join(random.sample(char, count))
                count -= count
    else:
        result = "".join(random.sample(char, length))

    # 是否大写
    if upper:
        return result.upper()
    else:
        return result


def hash256(data) -> str:
    """
    SHA-256 加密

    :param data: 需要加密的数据
    :return: 加密后的数据
    """
    try:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()
    except AttributeError:
        return hashlib.sha256(data).hexdigest()


def hash512(data) -> str:
    """
    SHA-512 加密

    :param data: 需要加密的数据
    :return: 加密后的数据
    """
    try:
        return hashlib.sha512(data.encode("utf-8")).hexdigest()
    except AttributeError:
        return hashlib.sha512(data).hexdigest()


def str_process(var):
    """字符串处理, 支持列表和字典"""
    if type(var) in [int, float, bool, None]:
        return var
    elif type(var) is str:
        return clean_str(var)
    elif type(var) in [list, tuple]:
        return [str_process(i) for i in var]
    elif type(var) is dict:
        return {str_process(k): str_process(v) for k, v in var.items()}
    else:
        return var


def clean_str(text: str) -> str:
    """去除异常字符"""
    text = eval(re.sub(r"\\u.{4}", "", repr(text)))  # 去除 unicode 编码
    text = eval(re.sub(r"\\x.{2}", "", repr(text)))  # 去除 hex 编码
    text = eval(re.sub(r"\\", "", repr(text)))  # 去除转义字符
    text = eval(re.sub(r"\"", "", repr(text)))  # 去除双引号
    text = eval(re.sub(r"\n", "", repr(text)))  # 去除换行符
    text = eval(re.sub(r"\r", "", repr(text)))  # 去除回车符
    text = eval(re.sub(r"\t", "", repr(text)))  # 去除制表符
    text = eval(re.sub(r"\s", "", repr(text)))  # 去除空格

    # 全角转半角
    new_string = ""
    for char in text:
        inside_code = ord(char)
        if inside_code == 0x3000:
            inside_code = 0x0020
        else:
            inside_code -= 0xFEE0

        # 不是半角字符返回原来的字符
        new_string += (
            char if inside_code < 0x0020 or inside_code > 0x7E else chr(inside_code)
        )

    return new_string
