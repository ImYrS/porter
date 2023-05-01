from getpass import getpass

import pymysql
from configobj import ConfigObj

from modules import common, password
from modules.database import db, User, VM, Rule


def create_db():
    """创建数据库"""
    config = ConfigObj('config.ini', encoding='utf-8')

    pydb = pymysql.connect(
        host=config['db']['host'],
        port=config['db'].as_int('port'),
        user=config['db']['user'],
        password=config['db']['password'],
    )
    cursor = pydb.cursor()
    cursor.execute(
        f'CREATE DATABASE IF NOT EXISTS '
        f'{config["db"]["database"]} '
        f'DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci;'
    )
    pydb.close()


def create_tables():
    """创建表"""
    db.connect()
    db.create_tables(
        [
            User,
            VM,
            Rule,
        ]
    )
    db.close()


def create_admin():
    """创建管理员"""
    User.create(
        username=input('Setting admin username: ').strip(),
        password=password.crypt(
            common.hash256(
                getpass('Setting admin password: ').strip()
            )
        ),
        is_admin=True,
        created_at=common.now(),
    )


def main():
    create_db()
    create_tables()
    create_admin()


if __name__ == '__main__':
    main()
