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
from configobj import ConfigObj

from modules import common
from modules.database import VM, Rule
from modules.decorator import auth_required
from modules.errors import Error, ErrorCodes

bp = blueprints.Blueprint('vms', __name__)

config = ConfigObj('./config.ini', encoding='utf-8')


def vm_to_dict(vm: VM, add_rules: Optional[bool] = False) -> dict:
    """将 VM 对象转换为 dict"""
    data = {
        'id': vm.id,
        'pve_id': vm.pve_id,
        'name': vm.name,
        'public_ip': config['core']['ip'],
        'private_ip': vm.ip,
        'ssh_port': vm.ssh_port,
        'created_at': vm.created_at,
        'rule_count': vm.rule_count,
        'rule_limit': vm.rule_limit,
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


def port_is_ok(port: int) -> bool:
    """检查端口是否合法"""
    try:
        return (
                10000 < port < 65536
                and
                not Rule.select().where(Rule.public_port == port).exists()
        )
    except peewee.PeeweeException as e:
        logging.error(f'检查端口是否合法失败: {e}')
        return False


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


@bp.route('/<int:vm_id>', methods=['GET'])
@auth_required()
def get_vm(vm_id: int) -> tuple[dict, int]:
    """获取虚拟机信息"""
    try:
        vm = VM.get(VM.id == vm_id, VM.user == g.user)
    except VM.DoesNotExist:
        return Error().not_found()

    except peewee.PeeweeException as e:
        logging.error(f'获取 VM 信息失败: {e}')
        return Error().db_error()

    return {
        'code': 200,
        'data': vm_to_dict(vm, add_rules=True)
    }, 200


@bp.route('/<int:vm_id>/rules', methods=['POST'])
@auth_required()
def create_rule(vm_id: int) -> tuple[dict, int]:
    """创建端口转发规则"""
    try:
        public_port = int(request.json['public_port'])
        private_port = int(request.json['private_port'])
        protocol = request.json['protocol'].lower()

        if protocol not in ('tcp', 'udp'):
            raise ValueError
    except (KeyError, TypeError, ValueError, BadRequest):
        return Error().parameters_invalid()

    try:
        if not port_is_ok(public_port):
            return Error(
                code=ErrorCodes.PortInvalid,
                http_code=409,
                message='Port invalid',
                message_human_readable='端口为保留端口或已被占用',
            ).create()

        vm = VM.get(VM.id == vm_id, VM.user == g.user)

        if vm.rule_count >= vm.rule_limit:
            return Error(
                code=ErrorCodes.RuleCountLimit,
                http_code=409,
                message='Rule count limit',
                message_human_readable='该虚拟机端口转发规则数量已达上限',
            ).create()

        rule = Rule.create(
            user=g.user,
            vm=vm,
            public_port=public_port,
            private_port=private_port,
            protocol=protocol,
            created_at=common.now(),
        )

        if private_port == 22:
            vm.ssh_port = public_port

        vm.rule_count += 1
        vm.save()

    except VM.DoesNotExist:
        return Error().not_found()

    except peewee.PeeweeException as e:
        logging.error(f'创建端口转发规则失败: {e}')
        return Error().db_error()

    return {
        'code': 200,
        'data': rule_to_dict(rule)
    }, 200


@bp.route('/<int:vm_id>/rules/<int:rule_id>', methods=['DELETE'])
@auth_required()
def delete_rule(vm_id: int, rule_id: int) -> tuple[dict, int]:
    """删除端口转发规则"""
    try:
        vm = VM.get(VM.id == vm_id, VM.user == g.user)
        rule = Rule.get(Rule.id == rule_id, Rule.vm == vm)
    except (VM.DoesNotExist, Rule.DoesNotExist):
        return Error().not_found()

    except peewee.PeeweeException as e:
        logging.error(f'删除端口转发规则失败: {e}')
        return Error().db_error()

    rule.delete_instance()
    vm.rule_count -= 1
    vm.save()

    return {'code': 200}, 210


@bp.route('/check_ip', methods=['POST'])
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


@bp.route('/check_port', methods=['POST'])
@auth_required()
def check_port() -> tuple[dict, int]:
    try:
        port = int(request.json['port'])
    except (KeyError, TypeError, ValueError, BadRequest):
        return Error().parameters_invalid()

    if not port_is_ok(port):
        return Error(
            code=ErrorCodes.PortInvalid,
            http_code=409,
            message='Port invalid',
            message_human_readable='端口为保留端口或已被占用',
        ).create()

    return {
        'code': 200,
        'data': {
            'port': port,
        }
    }, 200
