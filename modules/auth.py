"""
@Author: ImYrS Yang
@Date: 2023/2/12
@Copyright: ImYrS Yang
@Description:
"""

import logging

import peewee
from flask import request, Blueprint, g
from werkzeug.exceptions import BadRequest

from modules import common, password, session
from modules.database import User
from modules.decorator import auth_required
from modules.errors import Error, ErrorCodes

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["POST"])
def login() -> tuple[dict, int]:
    """登录接口"""
    try:
        username = request.json["username"].strip()
        pwd = request.json["password"]
    except (TypeError, KeyError, ValueError, BadRequest):
        return Error().parameters_invalid()

    try:
        user = User.get(User.username == username)
    except peewee.DoesNotExist:
        return Error(
            code=ErrorCodes.CredentialsInvalid,
            http_code=401,
            message="Credentials invalid",
            message_human_readable="账号不存在或密码错误",
        ).create()

    except peewee.PeeweeException as e:
        logging.error(f"用户查询失败: {e}")
        return Error().db_error()

    if not password.verify(pwd, user.password):
        return Error(
            code=ErrorCodes.CredentialsInvalid,
            http_code=401,
            message="Credentials invalid",
            message_human_readable="账号不存在或密码错误",
        ).create()

    token, expired_at = session.create(user=user)

    if not token or not expired_at:
        return Error().internal_error()

    return {
        "code": 0,
        "data": {"access_token": token, "expired_at": expired_at},
    }, 200


@bp.route("/reset-password", methods=["POST"])
@auth_required()
def reset_password() -> tuple[dict, int]:
    """重置密码"""
    try:
        old_pwd = request.json["old_password"]
        new_pwd = request.json["new_password"]
    except (TypeError, KeyError, ValueError, BadRequest):
        return Error().parameters_invalid()

    if not password.verify(old_pwd, g.user.password):
        return Error(
            code=ErrorCodes.CredentialsInvalid,
            http_code=409,
            message="Credentials invalid",
            message_human_readable="旧密码错误",
        ).create()

    try:
        g.user.password = password.crypt(new_pwd)
        g.user.save()
    except peewee.PeeweeException as e:
        logging.error(f"重置密码失败: {e}")
        return Error().db_error()

    return {"code": 0}, 200


@bp.route("/create-user", methods=["POST"])
@auth_required(is_admin=True)
def create_user() -> tuple[dict, int]:
    """创建用户"""
    try:
        username = request.json["username"].strip()
        pwd = request.json.get("password", None)
        is_admin = request.json.get("is_admin", False)
    except (TypeError, KeyError, ValueError, BadRequest):
        return Error().parameters_invalid()

    try:
        if User.select().where(User.username == username).exists():
            return Error(
                code=ErrorCodes.UserExists,
                http_code=409,
                message="Username exists",
                message_human_readable="用户名已存在",
            ).create()

        raw_pwd = None if pwd else common.rand_char(16)

        if raw_pwd:
            pwd = common.hash256(raw_pwd)

        user = User.create(
            username=username,
            password=password.crypt(pwd),
            is_admin=is_admin,
            created_at=common.now(),
        )

    except peewee.PeeweeException as e:
        logging.error(f"创建用户失败: {e}")
        return Error().db_error()

    return {
        "code": 0,
        "data": {
            "id": user.id,
            "username": user.username,
            "password": raw_pwd,
        },
    }, 200
