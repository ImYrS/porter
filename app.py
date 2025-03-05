"""
@Author: ImYrS Yang
@Date: 2023/2/12
@Copyright: ImYrS Yang
@Description:
"""

import logging
import os
from typing import Optional
from json import dumps

from configobj import ConfigObj
import peewee
from flask import Flask, g
from flask.json.provider import DefaultJSONProvider

from src import utils
from src.database import db
from src.formatter import add_camel_case_fields
from routers.v2 import bp as v2_bp


class BetterJSONProvider(DefaultJSONProvider):
    compact = True
    ensure_ascii = False
    mimetype = "application/json; charset=utf-8"


os.environ["NO_PROXY"] = "*"

app = Flask(__name__)

app.json = BetterJSONProvider(app)

app.register_blueprint(v2_bp, url_prefix="/v2")

config = ConfigObj("./config.ini", encoding="utf-8")
debug_mode = config["dev"].as_bool("debug")


def init_logger(debug: Optional[bool] = False):
    """初始化日志系统"""
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log_format = logging.Formatter(
        "%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s: %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if debug else logging.INFO)
    ch.setFormatter(log_format)
    log.addHandler(ch)

    if not os.path.exists("./logs/"):
        os.mkdir(os.getcwd() + "/logs/")

    log_name = f"./logs/{utils.formatted_time(secure_format=True)}.log"
    fh = logging.FileHandler(log_name, mode="a", encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(log_format)
    log.addHandler(fh)


init_logger(debug_mode)


@app.before_request
def before_request():
    g.db = db
    try:
        g.db.connect()
    except peewee.OperationalError as e:
        logging.error(f"数据库连接失败: {e}")


@app.after_request
def after_request(response):
    """请求后执行"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "86400"

    g.db.close()

    if response.is_json:
        data = response.json
        meta = data.get("meta", {})

        try:
            meta["user"] = {
                "id": g.user.id,
                "username": g.user.username,
                "is_admin": g.user.is_admin,
            }
        except AttributeError:
            pass

        # 处理 data 字段中的数据，添加小驼峰命名
        if "data" in data:
            data["data"] = add_camel_case_fields(data["data"])

        data["meta"] = meta
        response.set_data(dumps(data, ensure_ascii=False))
    return response


@app.teardown_request
def teardown_request(exception):
    """请求结束后执行"""
    if not g.db.is_closed():
        g.db.close()

    if exception:
        logging.error(f"[Teardown] {exception}")


@app.route("/<path:path>", methods=["OPTIONS"])
def options(path):
    return path, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500, debug=debug_mode)
