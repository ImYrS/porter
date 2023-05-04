"""
    @Author: ImYrS Yang
    @Date: 2023/4/20
    @Copyright: @ImYrS
"""

from functools import wraps
from typing import Optional

from flask import request

from modules import session
from modules.errors import Error


def auth_required(is_admin: Optional[bool] = False) -> callable:
    """
    Access Token 校验装饰器

    :return:
    """

    def decorated(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return Error().access_token_invalid()

            data = session.verify(token, is_admin)

            if isinstance(data, Error):
                return data.create()

            if not data:
                return Error().access_token_invalid()

            return func(*args, **kwargs)

        return wrapper

    return decorated
