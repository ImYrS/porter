import os
from getpass import getpass

from Crypto.PublicKey import RSA

from src import password, utils
from src.database import VM, Rule, User, db
from src.types import UserRoles


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
        username=input("Setting admin username: ").strip(),
        password=password.crypt(
            utils.hash256(getpass("Setting admin password: ").strip())
        ),
        role=UserRoles.ADMIN,
    )


def create_jwt_key():
    """创建 JWT 密钥"""
    key = RSA.generate(2048)

    os.makedirs("./keys", exist_ok=True)

    with open("./keys/jwt.pem", "wb") as f:
        f.write(key.export_key("PEM"))
    with open("./keys/jwt.pub", "wb") as f:
        f.write(key.publickey().export_key("PEM"))


def main(setup_admin: bool = True):
    create_tables()
    if setup_admin:
        create_admin()
    create_jwt_key()


if __name__ == "__main__":
    main()
