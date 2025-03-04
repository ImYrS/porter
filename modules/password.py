"""
@Author: ImYrS Yang
@Date: 2023/4/9
@Copyright: ImYrS Yang
@Description:
"""

import argon2


def crypt(password) -> str:
    """
    密码加密

    :param password: 需要加密的密码
    :return: 加密后的密码
    """
    return argon2.PasswordHasher().hash(password)


def verify(password, hashed) -> bool:
    """
    密码验证

    :param password: 需要验证的密码
    :param hashed: 加密后的密码
    :return: 验证结果
    """
    try:
        argon2.PasswordHasher().verify(hashed, password)
    except argon2.exceptions.VerificationError:
        return False

    return True
