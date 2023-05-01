"""
    @Author: ImYrS Yang
    @Date: 2023/4/21
    @Copyright: @ImYrS
"""

from typing import Optional
import logging

from flask import request, g, Blueprint
import jwt

from modules import common
from modules.database import User
from modules.errors import Error, ErrorCodes

bp = Blueprint('session', __name__)

pri_key = open('./keys/jwt.pem', 'r').read()
pub_key = open('./keys/jwt.pub', 'r').read()


def create(user: User) -> Optional[str]:
    """
    创建 Access Token

    :param user: User 对象
    :return: Access Token
    """
    expire_time = 60 * 60 * 24 * 1  # 1 天

    try:
        headers = {
            'typ': 'JWT',
            'alg': 'RS256',
        }

        payload = {
            'exp': common.timestamp(ms=False) + expire_time,
            'iat': common.timestamp(ms=False),
            'data': {
                'id': user.id,
                'username': user.username,
                'is_admin': user.is_admin,
            }
        }

        return jwt.encode(
            payload=payload,
            key=pri_key,
            algorithm='RS256',
            headers=headers
        )

    except Exception as e:
        logging.error(f'Access Token 生成失败: {e}')
        return None


def verify(token: str) -> dict | Error:
    """
    校验 Access Token

    :param token: Access Token
    :return: 校验结果
    """
    token = str(token or request.headers.get('Authorization'))

    token = token.replace('Bearer ', '')

    try:
        data = jwt.decode(
            jwt=token,
            key=pub_key,
            algorithms=['RS256'],
        )
    except jwt.exceptions.ExpiredSignatureError:
        return Error(
            code=ErrorCodes.AccessTokenExpired,
            http_code=401,
            message='Access token expired',
            message_human_readable='Access Token 已过期',
        )
    except jwt.exceptions.InvalidSignatureError:
        return {}
    except Exception as e:
        logging.error(f'Access Token 校验失败: {e}')
        return {}

    g.user_id = data['user_id']
    g.user = User.get(User.id == data['user_id'])

    return data
