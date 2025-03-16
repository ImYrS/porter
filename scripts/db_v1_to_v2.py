from peewee import (
    MySQLDatabase,
    SqliteDatabase,
)

import setup
from src.config import config
from src.database import VM, Rule, User
from src.types import RuleProtocols, UserRoles

old_db_conf = config["db_v1"]
old_db = (
    MySQLDatabase(
        old_db_conf["database"],
        host=old_db_conf["host"],
        user=old_db_conf["user"],
        passwd=old_db_conf["password"],
        port=old_db_conf.as_int("port"),
        autorollback=True,
        charset="utf8mb4",
    )
    if old_db_conf["type"] == "mysql"
    else SqliteDatabase(f"{old_db_conf['database']}.db")
)


def main():
    """迁移 v1 数据库到 v2"""
    setup.main(setup_admin=False)
    migrate_users()
    migrate_vms()
    migrate_rules()


def migrate_users():
    """迁移用户数据"""
    """
    username = CharField(32, unique=True)
    password = CharField(97)
    # diff
    - is_admin = BooleanField(default=False)
    + role = IntegerEnumField(UserRoles, default=UserRoles.USER)
    """
    for user in old_db.execute_sql(f"SELECT * FROM {old_db_conf['prefix']}user"):
        User.create(
            username=user[1],
            password=user[2],
            role=UserRoles.ADMIN if user[3] else UserRoles.USER,
            created_at=user[4],
        )


def migrate_vms():
    """迁移 VM 数据"""
    """
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
    # no diff
    """
    for vm in old_db.execute_sql(f"SELECT * FROM {old_db_conf['prefix']}vm"):
        VM.create(
            user=User.get(User.id == vm[1]),
            pve_id=vm[2],
            name=vm[3],
            ip=vm[4],
            ssh_port=vm[5],
            rule_count=vm[6],
            rule_limit=vm[7],
            created_at=vm[8],
        )


def migrate_rules():
    """迁移规则数据"""
    """
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
    # diff
    - protocol = CharField(4, default='tcp')
    + protocol = StringEnumField(RuleProtocols, default=RuleProtocols.TCP)
    """
    for rule in old_db.execute_sql(f"SELECT * FROM {old_db_conf['prefix']}rule"):
        # Get pve_id for the VM from old database
        vm_query = old_db.execute_sql(
            f"SELECT pve_id FROM {old_db_conf['prefix']}vm WHERE id = %s", (rule[2],)
        )
        old_pve_id = next(vm_query)[0]  # Get the pve_id from the query result

        Rule.create(
            user=User.get(User.id == rule[1]),
            vm=VM.get(VM.pve_id == old_pve_id),  # Find VM by pve_id instead of id
            public_port=rule[3],
            private_port=rule[4],
            protocol=RuleProtocols(rule[5]),
            created_at=rule[6],
        )


if __name__ == "__main__":
    main()
