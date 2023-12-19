"""
    @Author: ImYrS Yang
    @Date: 2023/2/12
    @Copyright: ImYrS Yang
    @Description: 
"""

import logging
import os
from typing import NoReturn, Optional

from configobj import ConfigObj
import peewee
from flask import Flask, g, request

from modules import common
from modules.database import db
from routers.backend_v1 import bp as backend_v1_bp
from routers.frontend_v1 import bp as frontend_v1_bp

os.environ['NO_PROXY'] = '*'

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.register_blueprint(backend_v1_bp, url_prefix='/api/v1')
app.register_blueprint(frontend_v1_bp, url_prefix='/')

config = ConfigObj('./config.ini', encoding='utf-8')
debug_mode = config['dev'].as_bool('debug')


def init_logger(debug: Optional[bool] = False):
    """初始化日志系统"""
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log_format = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s: %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if debug else logging.INFO)
    ch.setFormatter(log_format)
    log.addHandler(ch)

    if not os.path.exists('./logs/'):
        os.mkdir(os.getcwd() + '/logs/')

    log_name = f'./logs/{common.formatted_time(secure_format=True)}.log'
    fh = logging.FileHandler(log_name, mode='a', encoding='utf-8')
    fh.setLevel(logging.INFO)
    fh.setFormatter(log_format)
    log.addHandler(fh)


init_logger(debug_mode)


@app.before_request
def before_request():
    if request.path.startswith('/api/'):
        g.db = db
        try:
            g.db.connect()
        except peewee.OperationalError as e:
            logging.error(f'数据库连接失败: {e}')


@app.after_request
def after_request(response):
    """请求后执行"""
    if request.path.startswith('/api/'):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = '*'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '86400'

        g.db.close()
    return response


@app.teardown_request
def teardown_request(exception):
    """请求结束后执行"""
    if request.path.startswith('/api/'):
        if not g.db.is_closed():
            g.db.close()

    if exception:
        logging.error(f'[Teardown] {exception}')


@app.route('/<path:path>', methods=['OPTIONS'])
def options(path):
    return path, 200


@app.template_global()
def current_path_is(path, true='active', false='') -> str:
    """
    判断当前路径是否为指定路径

    :param path: 路径
    :param true: 结果为真时返回的值
    :param false: 结果为假时返回的值
    :return:
    """
    return (
        true
        if path == (
            request.path
            if not request.path[-1] == '/'
            else request.path[:-1]
        )
           or request.path.startswith(f'{path}/')
        else false
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500, debug=debug_mode)
