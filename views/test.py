import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from tietaja.database.db import get_db

bp = Blueprint('test', __name__, template_folder='templates')


@bp.route('/', methods=('GET', 'POST'))
def index():

    return render_template('index.html')


@bp.route('/hello', methods=('GET', 'POST'))
def hello():

    try:
        message = request.args['message']
    except:
        message = ""

    return render_template('hello.html', message=message)


@bp.route('/register/', methods=('GET', 'POST'))
def handle_data():
    username = request.form['username']
    password1 = request.form['password1']
    password2 = request.form['password2']

    if password1 != password2:
        return redirect(url_for('.hello'))

    db = get_db()

    try:

        db.execute(
            'INSERT INTO user (username, password) VALUES (?, ?)',
            (username, generate_password_hash(password1))
        )
    except:
        return redirect(url_for('.hello', message="Username already in use!"))

    db.commit()

    return redirect(url_for('.show_hello', username=username))


@bp.route('/show_hello/', methods=('GET', 'POST'))
def show_hello():

    username = request.args['username']

    return render_template('hello2.html', username=username)
