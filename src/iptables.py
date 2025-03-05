"""
@Author: ImYrS Yang
@Date: 2023/5/3
@Copyright: @ImYrS
"""

import logging
import os

from src.config import config
from src.database import Rule

interface = config["core"]["interface"]
iptables_file = config["core"]["iptables_file"]


def add(rule: Rule) -> bool:
    """
    添加规则

    :param rule:
    :return:
    """
    shell = (
        f"iptables -t nat -A PREROUTING -i {interface} "
        f"-p {rule.protocol} "
        f"--dport {rule.public_port} -j DNAT "
        f"--to-destination {rule.vm.ip}:{rule.private_port}"
    )

    logging.info(f"添加规则: {shell}")
    os.system(shell)

    with open(iptables_file, "a", encoding="utf-8") as f:
        f.write(shell + "\n")

    return True


def delete(rule: Rule) -> bool:
    """
    删除规则

    :param rule:
    :return:
    """
    shell = (
        f"iptables -t nat -D PREROUTING -i {interface} "
        f"-p {rule.protocol} "
        f"--dport {rule.public_port} -j DNAT "
        f"--to-destination {rule.vm.ip}:{rule.private_port}"
    )

    while os.system(shell) == 0:
        logging.info(f"删除规则: {shell}")

    shell = shell.replace("-D", "-A")

    with open(iptables_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(iptables_file, "w", encoding="utf-8") as f:
        for line in lines:
            if line != shell + "\n":
                f.write(line)

    return True
