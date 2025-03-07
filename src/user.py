"""
@Author: ImYrS Yang
@Date: 2025/3/5
@Copyright: @ImYrS
"""

from flask import blueprints, g

from src.decorator import auth_required

bp = blueprints.Blueprint("user", __name__)


@bp.route("/info", methods=["GET"])
@auth_required()
def check_port() -> tuple[dict, int]:
    return {
        "code": 0,
        "data": {
            "username": g.user.username,
            "user_id": g.user.id,
            "roles": [g.user.role.name],
        },
    }, 200
