"""
@Author: ImYrS Yang
@Date: 2023/4/12
@Copyright: ImYrS Yang
@Description:
"""

from flask import Blueprint

from src.auth import bp as auth_bp
from src.vm import bp as vm_bp
from src.errors import Error

bp = Blueprint("v2", __name__)


@bp.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def not_found(path):
    return Error().not_found()


bp.register_blueprint(auth_bp, url_prefix="/auth")
bp.register_blueprint(vm_bp, url_prefix="/vms")
