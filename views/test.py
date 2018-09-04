import functools
import requests
import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)

from werkzeug.security import check_password_hash, generate_password_hash

from tietaja.database.db import get_db

bp = Blueprint('test', __name__, template_folder='templates')


def login_required(f):

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'logged_in' in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/', methods=('GET', 'POST'))
def index():

    return render_template('index.html')


@bp.route('/home', methods=('GET', 'POST'))
@login_required
def home():

    return render_template('home.html')


@bp.route('/games', methods=('GET', 'POST'))
@login_required
def games():

    return render_template('games.html')


@bp.route('/user_info', methods=('GET', 'POST'))
@login_required
def user_info():

    return render_template('user_info.html')


@bp.route('/login_page', methods=('GET', 'POST'))
def login_page():

    return render_template('login.html')


@bp.route('/register_page', methods=('GET', 'POST'))
def register_page():

    try:
        message = request.args['message']
    except:
        message = ""

    return render_template('register.html', message=message)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        error = None

        db = get_db()

        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session['user_id'] = user['id']
            session['username'] = username
            session['logged_in'] = True
            g.user = user
            return redirect(url_for('.home'))

        # flash(error) #TODO

    return render_template('/login.html', message=error)


@bp.route('/register', methods=('GET', 'POST'))
def register():
    username = request.form['username']
    password1 = request.form['password1']
    password2 = request.form['password2']

    if password1 != password2:
        return redirect(url_for('.register_page', message="Passwords did not match"))

    db = get_db()

    try:

        db.execute(
            'INSERT INTO user (username, password) VALUES (?, ?)',
            (username, generate_password_hash(password1))
        )
    except:
        return redirect(url_for('.register_page', message="Username already in use!"))

    db.commit()

    user = db.execute('SELECT * FROM user WHERE username = ?',
                      (username,)).fetchone()

    session['user_id'] = user['id']
    session['username'] = username
    session['logged_in'] = True

    return redirect(url_for('.home'))


@bp.route('/logout', methods=('GET', 'POST'))
def logout():
    session.clear()
    return render_template('/index.html')


@bp.route('/select_new_game_dates', methods=('GET', 'POST'))
def select_new_game_dates():
    return render_template('/select_new_game_dates.html')


@bp.route('/select_included_games', methods=('GET', 'POST'))
def select_included_games():
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")

    uri = "https://statsapi.web.nhl.com/api/v1/schedule?startDate=" + \
        start_date+"&endDate="+end_date
    try:
        uResponse = requests.get(uri)
    except requests.ConnectionError:
        return "Connection Error"
    Jresponse = uResponse.text
    data = json.loads(Jresponse)

    d = {}
    home = ""
    away = ""

    print(data['totalGames'])
    for date in data['dates']:
        for game in date['games']:
            gameId = game['gamePk']
            for key, value in game['teams'].items():
                if key == 'away':
                    away = value['team']['name']
                elif key == 'home':
                    home = value['team']['name']
                d[gameId] = home + ' - ' + away

    # TODO: Get games based on start and end dates

    return render_template('/select_included_games.html', startDate=start_date, endDate=end_date, d=d)
