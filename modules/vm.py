"""
    @Author: ImYrS Yang
    @Date: 2023/5/2
    @Copyright: @ImYrS
"""

import logging
from typing import Optional

import peewee
from flask import g, blueprints, request
from werkzeug.exceptions import BadRequest

from modules import common
from modules.database import VM, Rule
from modules.decorator import auth_required
from modules.errors import Error, ErrorCodes

bp = blueprints.Blueprint('vms', __name__)


def vm_to_dict(vm: VM, add_rules: Optional[bool] = False) -> dict:
    """将 VM 对象转换为 dict"""
    data = {
        'id': vm.id,
        'pve_id': vm.pve_id,
        'name': vm.name,
        'ip': vm.ip,
        'ssh_port': vm.ssh_port,
        'created_at': vm.created_at,
        'rules_count': vm.rules.count(),
        'rules': None,
    }

    if add_rules:
        data['rules'] = [
            rule_to_dict(rule)
            for rule in vm.rules
        ]

    return data


def rule_to_dict(rule: Rule) -> dict:
    """将 Rule 对象转换为 dict"""
    return {
        'id': rule.id,
        'public_port': rule.public_port,
        'private_port': rule.private_port,
        'protocol': rule.protocol,
        'created_at': rule.created_at,
    }


@bp.route('', methods=['GET'])
@auth_required()
def get_vms() -> tuple[dict, int]:
    """获取虚拟机列表"""
    try:
        vms = VM.select().where(VM.user == g.user)
    except peewee.PeeweeException as e:
        logging.error(f'获取 VM 列表失败: {e}')
        return Error().db_error()

    return {
        'code': 200,
        'data': [
            vm_to_dict(vm)
            for vm in vms
        ]
    }, 200


@bp.route('', methods=['POST'])
@auth_required()
def create_vm() -> tuple[dict, int]:
    try:
        name = request.json.get('name', None)
        pve_id = int(request.json['pve_id'])
        ip = request.json['ip']
    except (KeyError, TypeError, ValueError, BadRequest):
        return Error().parameters_invalid()

    try:
        if VM.select().where(VM.pve_id == pve_id).exists():
            return Error(
                code=ErrorCodes.PVEIDExists,
                http_code=409,
                message='PVE ID exists',
                message_human_readable='PVE ID 已存在',
            ).create()

        vm = VM.create(
            user=g.user,
            name=name,
            pve_id=pve_id,
            ip=ip,
            created_at=common.now(),
        )

    except peewee.IntegrityError:
        return Error(
            code=ErrorCodes.IPExists,
            http_code=409,
            message='IP exists',
            message_human_readable='IP 已存在',
        ).create()

    except peewee.PeeweeException as e:
        logging.error(f'创建 VM 失败: {e}')
        return Error().db_error()

    return {
        'code': 200,
        'data': vm_to_dict(vm)
    }, 200


@bp.route('/ip_check', methods=['POST'])
@auth_required()
def check_ip() -> tuple[dict, int]:
    try:
        ip = request.json['ip']
    except (KeyError, TypeError, BadRequest):
        return Error().parameters_invalid()

    try:
        if VM.select().where(VM.ip == ip).exists():
            return Error(
                code=ErrorCodes.IPExists,
                http_code=409,
                message='IP exists',
                message_human_readable='IP 已存在',
            ).create()

    except peewee.PeeweeException as e:
        logging.error(f'检查 IP 是否存在失败: {e}')
        return Error().db_error()

    return {
        'code': 200,
        'data': {
            'ip': ip,
        }
    }, 200
