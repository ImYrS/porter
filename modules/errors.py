"""
@Author: ImYrS Yang
@Date: 2023/2/14
@Copyright: ImYrS Yang
@Description:
"""

from typing import Optional

from flask import request


class Error:

    def __init__(
        self,
        code: Optional[int] = None,
        http_code: Optional[int] = 400,
        message: Optional[str] = None,
        message_human_readable: Optional[str] = None,
        data: Optional[dict] = None,
    ):
        """
        错误类

        :param code: 错误码
        :param http_code: HTTP 状态码
        :param message: 错误信息, 英文的广义描述
        :param message_human_readable: 错误信息, 中文可读的狭义描述
        :param data: 可返回的数据
        """
        self.code = code
        self.http_code = http_code or 400
        self.message = message
        self.message_human_readable = message_human_readable
        self.data = data or {
            "path": request.path,
            "method": request.method,
        }

    def create(self) -> tuple[dict, int]:
        """创建 HTTP 响应数据"""
        return {
            "code": self.code,
            "message": self.message,
            "message_human_readable": self.message_human_readable,
            "data": self.data,
        }, self.http_code

    def parameters_invalid(self) -> tuple[dict, int]:
        """请求参数缺失或不可用"""
        self.code = self.http_code = 400
        self.message = "Parameters invalid"
        self.message_human_readable = "请求参数缺失或不可用"

        return self.create()

    def db_error(self) -> tuple[dict, int]:
        """数据库错误"""
        self.code = self.http_code = 500
        self.message = "Database error"
        self.message_human_readable = "数据库错误"

        return self.create()

    def access_token_invalid(self) -> tuple[dict, int]:
        """会话无效"""
        self.code = ErrorCodes.AccessTokenInvalid
        self.http_code = 401
        self.message = "Access token invalid"
        self.message_human_readable = "会话无效, 可能已经过期"

        return self.create()

    def permission_denied(self) -> tuple[dict, int]:
        """权限不足"""
        self.code = self.http_code = 403
        self.message = "Permission denied"
        self.message_human_readable = "权限不足"

        return self.create()

    def not_found(self) -> tuple[dict, int]:
        """资源不存在"""
        self.code = self.http_code = 404
        self.message = "Not found"
        self.message_human_readable = "资源不存在"

        return self.create()

    def internal_error(self) -> tuple[dict, int]:
        """内部错误"""
        self.code = self.http_code = 500
        self.message = "Internal error"
        self.message_human_readable = "内部错误, 请稍后再试"

        return self.create()


class ErrorCodes:
    CredentialsInvalid = 1011
    AccessTokenInvalid = 1012
    AccessTokenExpired = 1013
    UserExists = 1014
    PVEIDExists = 1021
    IPExists = 1022
    PortInvalid = 1023
    RuleCountLimit = 1024
