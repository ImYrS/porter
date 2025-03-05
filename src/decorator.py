"""
@Author: ImYrS Yang
@Date: 2023/4/20
@Copyright: @ImYrS
"""

from functools import wraps
from typing import Optional

from flask import request

from src import session
from src.errors import Error


def auth_required(is_admin: Optional[bool] = False) -> callable:
    """
    Access Token 校验装饰器

    :return:
    """

    def decorated(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = request.headers.get("Authorization", "").strip("Bearer ")
            if not token:
                return Error().session_invalid().create()

            data = session.verify(token, is_admin)

            if isinstance(data, Error):
                return data.create()

            if not data:
                return Error().session_invalid().create()

            return func(*args, **kwargs)

        return wrapper

    return decorated
