from peewee import *
from configobj import ConfigObj

config = ConfigObj('config.ini', encoding='utf-8')

db = (
    MySQLDatabase(
        config['db']['database'],
        host=config['db']['host'],
        user=config['db']['user'],
        passwd=config['db']['password'],
        port=config['db'].as_int('port'),
        autorollback=True,
        charset='utf8mb4',
    )
    if config['db']["type"] == "mysql"
    else SqliteDatabase(f"{config['db']['database']}.db")
)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    id = PrimaryKeyField()
    username = CharField(32, unique=True)
    password = CharField(97)
    is_admin = BooleanField(default=False)
    created_at = BigIntegerField(default=0)

    class Meta:
        db_table = config['db']['prefix'] + 'user'


class VM(BaseModel):
    id = PrimaryKeyField()
    user = ForeignKeyField(
        User,
        backref='vms',
        on_delete='CASCADE',
        on_update='CASCADE',
        column_name='user_id',
    )
    pve_id = IntegerField(default=0, unique=True)
    name = CharField(32, default=None, null=True)
    ip = CharField(15, unique=True)
    ssh_port = IntegerField(default=None, null=True)
    rule_count = IntegerField(default=0)
    rule_limit = IntegerField(default=20)
    created_at = BigIntegerField(default=0)

    class Meta:
        db_table = config['db']['prefix'] + 'vm'


class Rule(BaseModel):
    id = PrimaryKeyField()
    user = ForeignKeyField(
        User,
        backref='rules',
        on_delete='CASCADE',
        on_update='CASCADE',
        column_name='user_id',
    )
    vm = ForeignKeyField(
        VM,
        backref='rules',
        on_delete='CASCADE',
        on_update='CASCADE',
        column_name='vm_id',
    )
    public_port = IntegerField(default=0)
    private_port = IntegerField(default=0)
    protocol = CharField(4, default='tcp')
    created_at = BigIntegerField(default=0)

    class Meta:
        db_table = config['db']['prefix'] + 'rule'
