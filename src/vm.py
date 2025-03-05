"""
@Author: ImYrS Yang
@Date: 2023/5/2
@Copyright: @ImYrS
"""

import logging
from typing import Optional

import peewee
from flask import blueprints, g, request
from werkzeug.exceptions import BadRequest

from src import iptables, utils
from src.config import config
from src.database import VM, Rule, User
from src.decorator import auth_required
from src.errors import Error
from src.types import UserRoles

bp = blueprints.Blueprint("vms", __name__)


def get_vm(vm_id: int, user: User = g.user) -> Optional[VM]:
    """
    获取 VM 对象

    如果用户角色为管理员，可以获取到不属于自己的 VM 对象

    :param vm_id: VM ID
    :param user: User 对象，默认为 g.user
    :return: VM 对象
    """

    try:
        return VM.get(
            VM.id == vm_id,
            (True if user.role == UserRoles.ADMIN else (VM.user == user)),
        )
    except peewee.DoesNotExist:
        return None
    except peewee.PeeweeException as e:
        logging.error(f"获取 VM 失败: {e}")
        raise e


def vm_to_dict(vm: VM, add_rules: Optional[bool] = False) -> dict:
    """将 VM 对象转换为 dict"""
    data = {
        "id": vm.id,
        "pve_id": vm.pve_id,
        "name": vm.name,
        "public_ip": config["core"]["ip"],
        "private_ip": vm.ip,
        "ssh_port": vm.ssh_port,
        "created_at": vm.created_at,
        "rule_count": vm.rule_count,
        "rule_limit": vm.rule_limit,
        "rules": None,
        "user": {
            "id": vm.user.id,
            "username": vm.user.username,
            "roles": [UserRoles(vm.user.role).name],
        },
    }

    if add_rules:
        data["rules"] = [rule_to_dict(rule) for rule in vm.rules]

    return data


def rule_to_dict(rule: Rule) -> dict:
    """将 Rule 对象转换为 dict"""
    return {
        "id": rule.id,
        "public_port": rule.public_port,
        "private_port": rule.private_port,
        "protocol": rule.protocol,
        "created_at": rule.created_at,
    }


def port_is_ok(port: int, protocol: str, bypass_limit: bool = False) -> bool:
    """检查端口是否合法"""
    try:
        # Check if port is within allowed range (unless bypassing limits)
        port_in_valid_range = True if bypass_limit else (10000 < port < 65536)

        # Check if port is already in use for the given protocol
        port_not_in_use = (
            not Rule.select()
            .where(Rule.public_port == port, Rule.protocol == protocol)
            .exists()
        )

        return port_in_valid_range and port_not_in_use
    except peewee.PeeweeException as e:
        logging.error(f"检查端口是否合法失败: {e}")
        return False


@bp.route("", methods=["GET"])
@auth_required()
def get_vms() -> tuple[dict, int]:
    """获取虚拟机列表"""
    try:
        vms = (
            VM.select()
            .where(VM.user == g.user)
            .join(User)
            .order_by(VM.created_at.desc())
        )
    except peewee.PeeweeException as e:
        logging.error(f"获取 VM 列表失败: {e}")
        return Error().internal_server_error().create()

    return {"code": 0, "data": [vm_to_dict(vm) for vm in vms]}, 200


@bp.route("", methods=["POST"])
@auth_required()
def create_vm() -> tuple[dict, int]:
    try:
        name = request.json.get("name", None)
        pve_id = int(request.json["pve_id"])
        ip = request.json["ip"]
    except (KeyError, TypeError, ValueError, BadRequest):
        return Error().parameters_invalid().create()

    try:
        if VM.select().where(VM.pve_id == pve_id).exists():
            return Error(
                code=-1,
                http_code=409,
                message="PVE ID exists",
                message_human_readable="PVE ID 已存在",
            ).create()

        vm = VM.create(
            user=g.user,
            name=name,
            pve_id=pve_id,
            ip=ip,
            created_at=utils.now(),
        )

    except peewee.IntegrityError:
        return Error(
            code=-1,
            http_code=409,
            message="IP exists",
            message_human_readable="IP 已存在",
        ).create()

    except peewee.PeeweeException as e:
        logging.error(f"创建 VM 失败: {e}")
        return Error().internal_server_error().create()

    return {"code": 0, "data": vm_to_dict(vm)}, 200


@bp.route("/<int:vm_id>", methods=["GET"])
@auth_required()
def get_vm(vm_id: int) -> tuple[dict, int]:
    """获取虚拟机信息"""
    try:
        vm = get_vm(vm_id)
        if not vm:
            return Error().not_found().create()
    except peewee.PeeweeException:
        return Error().internal_server_error().create()

    return {"code": 0, "data": vm_to_dict(vm, add_rules=True)}, 200


@bp.route("/<int:vm_id>", methods=["DELETE"])
@auth_required()
def delete_vm(vm_id: int) -> tuple[dict, int]:
    """删除虚拟机"""
    try:
        vm = get_vm(vm_id)
        if not vm:
            return Error().not_found().create()
    except peewee.PeeweeException:
        return Error().internal_server_error().create()

    for rule in vm.rules:
        iptables.delete(rule)
        rule.delete_instance()

    vm.delete_instance()

    return {"code": 0}, 210


@bp.route("/<int:vm_id>/rules", methods=["POST"])
@auth_required()
def create_rule(vm_id: int) -> tuple[dict, int]:
    """创建端口转发规则"""
    try:
        public_port = int(request.json["public_port"])
        private_port = int(request.json["private_port"])
        protocol = request.json["protocol"].lower()

        if protocol not in ("tcp", "udp"):
            raise ValueError
    except (KeyError, TypeError, ValueError, BadRequest):
        return Error().parameters_invalid().create()

    try:
        if not port_is_ok(
            public_port, protocol, bypass_limit=g.user.role == UserRoles.ADMIN
        ):
            return Error(
                code=-1,
                http_code=409,
                message="Port invalid",
                message_human_readable="端口为保留端口或已被占用",
            ).create()

        vm = get_vm(vm_id)
        if not vm:
            return Error().not_found().create()

        if vm.rule_count >= vm.rule_limit:
            return Error(
                code=-1,
                http_code=409,
                message="Rule count limit",
                message_human_readable="该虚拟机端口转发规则数量已达上限",
            ).create()

        rule = Rule.create(
            user=g.user,
            vm=vm,
            public_port=public_port,
            private_port=private_port,
            protocol=protocol,
            created_at=utils.now(),
        )

        if private_port == 22:
            vm.ssh_port = public_port

        vm.rule_count += 1
        vm.save()

        iptables.add(rule)

    except peewee.PeeweeException as e:
        logging.error(f"创建端口转发规则失败: {e}")
        return Error().internal_server_error().create()

    return {"code": 0, "data": rule_to_dict(rule)}, 200


@bp.route("/<int:vm_id>/rules/<int:rule_id>", methods=["DELETE"])
@auth_required()
def delete_rule(vm_id: int, rule_id: int) -> tuple[dict, int]:
    """删除端口转发规则"""
    try:
        vm = get_vm(vm_id)
        if not vm:
            return Error().not_found().create()

        rule = Rule.get(Rule.id == rule_id, Rule.vm == vm)

    except peewee.DoesNotExist:
        return Error().not_found().create()

    except peewee.PeeweeException as e:
        logging.error(f"删除端口转发规则失败: {e}")
        return Error().internal_server_error().create()

    iptables.delete(rule)

    if rule.private_port == 22:
        vm.ssh_port = None

    rule.delete_instance()
    vm.rule_count -= 1
    vm.save()

    return {"code": 0}, 210


@bp.route("/check_ip", methods=["POST"])
@auth_required()
def check_ip() -> tuple[dict, int]:
    try:
        ip = request.json["ip"]
    except (KeyError, TypeError, BadRequest):
        return Error().parameters_invalid().create()

    try:
        if VM.select().where(VM.ip == ip).exists():
            return Error(
                code=-1,
                http_code=409,
                message="IP exists",
                message_human_readable="IP 已存在",
            ).create()

    except peewee.PeeweeException as e:
        logging.error(f"检查 IP 是否存在失败: {e}")
        return Error().internal_server_error().create()

    return {
        "code": 0,
        "data": {
            "ip": ip,
        },
    }, 200


@bp.route("/check_port", methods=["POST"])
@auth_required()
def check_port() -> tuple[dict, int]:
    try:
        port = int(request.json["port"])
        protocol = request.json["protocol"].lower()
    except (KeyError, TypeError, ValueError, BadRequest):
        return Error().parameters_invalid().create()

    if not port_is_ok(port, protocol, bypass_limit=g.user.role == UserRoles.ADMIN):
        return Error(
            code=-1,
            http_code=409,
            message="Port invalid",
            message_human_readable="端口为保留端口或已被占用",
        ).create()

    return {
        "code": 0,
        "data": {
            "port": port,
        },
    }, 200
