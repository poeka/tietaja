import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from tietaja.database.db import get_db

bp = Blueprint('test', __name__, template_folder='templates')


@bp.route('/hello', methods=('GET', 'POST'))
def hello():
    return render_template('hello.html')


@bp.route('/register/', methods=('GET', 'POST'))
def handle_data():
    username = request.form['username']
    password1 = request.form['password1']
    password2 = request.form['password2']

    if password1 != password2:
        return redirect(url_for('.hello'))

    db = get_db()

    db.execute(
        'INSERT INTO user (username, password) VALUES (?, ?)',
        (username, generate_password_hash(password1))
    )

    db.commit()

    return redirect(url_for('.show_hello', username=username))


@bp.route('/show_hello/', methods=('GET', 'POST'))
def show_hello():

    username = request.args['username']

    return render_template('hello2.html', username=username)
