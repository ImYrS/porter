"""
    @Author: ImYrS Yang
    @Date: 2023/2/12
    @Copyright: ImYrS Yang
    @Description:
"""

import logging

import peewee
from flask import request, Blueprint
from werkzeug.exceptions import BadRequest

from modules import common, password, session
from modules.database import User
from modules.errors import Error, ErrorCodes

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['POST'])
def login() -> tuple[dict, int]:
    """登录接口"""
    try:
        username = request.json['username'].strip()
        pwd = request.json['password']
    except (TypeError, KeyError, ValueError, BadRequest):
        return Error().parameters_invalid()

    try:
        user = User.get(User.username == username)
    except peewee.DoesNotExist:
        return Error(
            code=ErrorCodes.CredentialsInvalid,
            http_code=401,
            message='Credentials invalid',
            message_human_readable='账号不存在或密码错误'
        ).create()

    except peewee.PeeweeException as e:
        logging.error(f'用户查询失败: {e}')
        return Error().db_error()

    if not password.verify(pwd, user.password):
        return Error(
            code=ErrorCodes.CredentialsInvalid,
            http_code=401,
            message='Credentials invalid',
            message_human_readable='账号不存在或密码错误'
        ).create()

    return session.create(user=user)
