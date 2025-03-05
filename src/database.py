from peewee import (
    BigIntegerField,
    CharField,
    Field,
    ForeignKeyField,
    IntegerField,
    Model,
    MySQLDatabase,
    PrimaryKeyField,
    SqliteDatabase,
)

from src import utils
from src.config import config
from src.types import RuleProtocols, UserRoles

db = (
    MySQLDatabase(
        config["db"]["database"],
        host=config["db"]["host"],
        user=config["db"]["user"],
        passwd=config["db"]["password"],
        port=config["db"].as_int("port"),
        autorollback=True,
        charset="utf8mb4",
    )
    if config["db"]["type"] == "mysql"
    else SqliteDatabase(f"{config['db']['database']}.db")
)


class EnumField(Field):
    """枚举字段基类"""

    def __init__(self, enum_class, *args, **kwargs):
        self.enum_class = enum_class
        super().__init__(*args, **kwargs)

    def db_value(self, value):
        """将 Enum 实例转换为可存储的值"""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value
        return value

    def python_value(self, value):
        """将数据库中的值转换为 Enum 实例"""
        if value is None:
            return None
        try:
            return self.enum_class(value)
        except ValueError:
            # 处理无效的枚举值
            return None


class IntegerEnumField(EnumField, IntegerField):
    """整数枚举字段"""

    pass


class StringEnumField(EnumField, CharField):
    """字符串枚举字段"""

    pass


class BaseModel(Model):
    id = PrimaryKeyField()
    created_at = BigIntegerField(default=0)
    updated_at = BigIntegerField(default=0)

    @classmethod
    def create(cls, **kwargs):
        kwargs["created_at"] = kwargs.get("created_at", utils.now())
        return super(BaseModel, cls).create(**kwargs)

    def save(self, *args, **kwargs):
        self.updated_at = utils.now()
        return super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        database = db


class User(BaseModel):
    username = CharField(32, unique=True)
    password = CharField(97)
    role = IntegerEnumField(UserRoles, default=UserRoles.USER)

    class Meta:
        db_table = config["db"]["prefix"] + "user"


class VM(BaseModel):
    user = ForeignKeyField(
        User,
        backref="vms",
        on_delete="CASCADE",
        on_update="CASCADE",
        column_name="user_id",
    )
    pve_id = IntegerField(default=0, unique=True)
    name = CharField(32, default=None, null=True)
    ip = CharField(15, unique=True)
    ssh_port = IntegerField(default=None, null=True)
    rule_count = IntegerField(default=0)
    rule_limit = IntegerField(default=20)

    class Meta:
        db_table = config["db"]["prefix"] + "vm"


class Rule(BaseModel):
    user = ForeignKeyField(
        User,
        backref="rules",
        on_delete="CASCADE",
        on_update="CASCADE",
        column_name="user_id",
    )
    vm = ForeignKeyField(
        VM,
        backref="rules",
        on_delete="CASCADE",
        on_update="CASCADE",
        column_name="vm_id",
    )
    public_port = IntegerField(default=0)
    private_port = IntegerField(default=0)
    protocol = StringEnumField(RuleProtocols, default=RuleProtocols.TCP)

    class Meta:
        db_table = config["db"]["prefix"] + "rule"
