import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

bp = Blueprint('test', __name__, template_folder='templates')


@bp.route('/hello', methods=('GET', 'POST'))
def hello():
    return render_template('hello.html')

@bp.route('/handle_data/', methods=('GET', 'POST'))
def handle_data():
    first_name = request.form['firstname']
    last_name = request.form['lastname']

    return redirect(url_for('.show_hello', firstname=first_name, lastname=last_name))

@bp.route('/show_hello/', methods=('GET', 'POST'))
def show_hello():
    
    first_name = request.args['firstname']
    last_name = request.args['lastname']
    
    return render_template('hello2.html', firstname=first_name, lastname=last_name)
