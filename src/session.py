"""
@Author: ImYrS Yang
@Date: 2023/4/21
@Copyright: @ImYrS
"""

import logging
from typing import Optional

import jwt
from flask import g, request

from src import utils
from src.database import User
from src.errors import Error
from src.types import UserRoles

pri_key = open("./keys/jwt.pem", "r").read()
pub_key = open("./keys/jwt.pub", "r").read()


def create(user: User) -> (Optional[str], int):
    """
    创建 Access Token

    :param user: User 对象
    :return: Access Token 和过期时间
    """
    expire_time = 60 * 60 * 24 * 1  # 1 天

    try:
        headers = {
            "typ": "JWT",
            "alg": "RS256",
        }

        expired_at = utils.timestamp(ms=False) + expire_time

        payload = {
            "exp": expired_at,
            "iat": utils.timestamp(ms=False),
            "data": {
                "id": user.id,
                "username": user.username,
                "roles": [UserRoles(user.role).name],
            },
        }

        return (
            jwt.encode(
                payload=payload, key=pri_key, algorithm="RS256", headers=headers
            ),
            expired_at,
        )

    except Exception as e:
        logging.error(f"Access Token 生成失败: {e}")
        return None, 0


def verify(token: str, is_admin: Optional[bool] = False) -> dict or Error:
    """
    校验 Access Token

    :param token: Access Token
    :param is_admin: 是否需要管理员权限
    :return: 校验结果
    """
    token = str(token or request.headers.get("Authorization"))

    token = token.replace("Bearer ", "")

    try:
        data = jwt.decode(
            jwt=token,
            key=pub_key,
            algorithms=["RS256"],
        )
    except jwt.exceptions.ExpiredSignatureError:
        return Error(
            code=-1,
            http_code=401,
            message="Access token expired",
            message_human_readable="Access Token 已过期",
        )
    except jwt.exceptions.InvalidSignatureError:
        return {}
    except Exception as e:
        logging.error(f"Access Token 校验失败: {e}")
        return {}

    if is_admin and not data["data"]["is_admin"]:
        return Error(
            code=403,
            http_code=403,
            message="Permission denied",
            message_human_readable="权限不足",
        )

    g.user_id = data["data"]["id"]
    g.is_admin = data["data"]["is_admin"]
    g.user = User.get(User.id == g.user_id)

    return data
