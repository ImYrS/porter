"""
@Author: ImYrS Yang
@Date: 2025/3/5
@Copyright: ImYrS Yang
@Description: 格式化工具
"""


def to_camel_case(snake_str: str) -> str:
    """
    将下划线命名转换为小驼峰命名

    :param snake_str: 下划线命名字符串
    :return: 小驼峰命名字符串
    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def add_camel_case_fields(data):
    """
    递归地为字典中的所有键添加小驼峰命名版本

    :param data: 要处理的数据
    :return: 处理后的数据
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # 将值递归处理
            processed_value = add_camel_case_fields(value)
            # 保留原始下划线命名的键值对
            result[key] = processed_value
            # 添加小驼峰命名的键值对（如果与原始键不同）
            camel_key = to_camel_case(key)
            if camel_key != key:
                result[camel_key] = processed_value
        return result
    elif isinstance(data, list):
        return [add_camel_case_fields(item) for item in data]
    else:
        return data
