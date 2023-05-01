
from flask import Blueprint, render_template, redirect

bp = Blueprint('frontend', __name__)


@bp.route('/')
def index():
    return redirect('/auth/login')


@bp.route('/auth/login', strict_slashes=False)
def login():
    return render_template('auth/sign-in.html')


@bp.route('/user/vms', strict_slashes=False)
def user_vms():
    return render_template('user/vms.html')
