import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

bp = Blueprint('test', __name__, template_folder='templates')


@bp.route('/hello', methods=('GET', 'POST'))
def hello():
    return render_template('hello.html')
