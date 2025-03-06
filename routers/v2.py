"""
@Author: ImYrS Yang
@Date: 2023/4/12
@Copyright: ImYrS Yang
@Description:
"""

from flask import Blueprint

from src import auth, user, vm
from src.errors import Error

bp = Blueprint("v2", __name__)


@bp.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def not_found(path):
    return Error().not_found().create()


bp.register_blueprint(auth.bp, url_prefix="/auth")
bp.register_blueprint(user.bp, url_prefix="/user")
bp.register_blueprint(vm.bp, url_prefix="/vms")
