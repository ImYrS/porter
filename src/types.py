from enum import Enum


class UserRoles(Enum):
    ADMIN = 100
    USER = 1


class RuleProtocols(Enum):
    TCP = "tcp"
    UDP = "udp"
