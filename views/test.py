import functools
import requests
import json


from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)

from werkzeug.security import check_password_hash, generate_password_hash

from tietaja.database.db import get_db
from random import randint

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

    db = get_db()
    userCreated = db.execute(
        # Own games
        'SELECT * FROM game WHERE creator = ?', (session['user_id'],)).fetchall()

    userJoined = db.execute(
        # Joined games
        'SELECT * FROM joined WHERE player = ?', (session['user_id'],)).fetchall()

    return render_template('games.html', userCreated=userCreated, userJoined=userJoined)


@bp.route('/user_info', methods=('GET', 'POST'))
@login_required
def user_info():

    return render_template('user_info.html')


@bp.route('/game', methods=('GET', 'POST'))
@login_required
def game():

    if request.method == 'POST':

        print(request.form.getlist('selected[]'))

        try:
            selected = request.form.getlist('selected[]')
            gameid = randint(10000, 99999)
            user_id = session['user_id']

            db = get_db()
            db.execute(
                'INSERT INTO game (game_id, creator) VALUES (?, ?)',
                (gameid, user_id)
            )

            for matchid in selected:
                db.execute(
                    'INSERT INTO match (match_id, game_id) VALUES (?, ?)',
                    (matchid, gameid)
                )
            db.commit()
            print('done')
            return render_template('game.html', games=selected)

        except:
            print('error')

            return redirect(url_for('.home'))

    else:
        try:
            gameId = request.args['gameId']
        except:
            return redirect(url_for('.games'))

        db = get_db()
        games = db.execute('SELECT * FROM match WHERE game_id = ?',
                           (gameId,)).fetchall()

        if len(games) > 0:
            selected = []
            for game in games:
                selected.append(game['match_id'])

            return render_template('game.html', games=selected)

        return redirect(url_for('.games'))


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


@bp.route('/join_game', methods=('GET', 'POST'))
@login_required
def join_game():
    return render_template('/join_game.html')


@bp.route('/join', methods=('GET', 'POST'))
@login_required
def join():

    gameId = int(request.args.get("gameId"))

    db = get_db()

    # Check if the game to be joined is created by the user
    # There can be only one game with this game ID

    gameToJoin = db.execute('SELECT * FROM game WHERE game_id = ?',
                            (gameId,)).fetchone()

    if gameToJoin == None:
        print('Game does not exist.')
        return redirect(url_for('.games'))

    if gameToJoin['creator'] == session['user_id']:
        print("Own game! No need to join.")
        return redirect(url_for('.games'))

    # Check that the user has not joined the game yet

    game = db.execute('SELECT * FROM joined WHERE game_id = ? AND player = ?',
        (gameId, session['user_id'])).fetchone()

    if game:
        return redirect(url_for('.games'))

    db.execute(
        'INSERT INTO joined (game_id, player) VALUES (?, ?)',
        (gameId, session['user_id'])
    )
    db.commit()

    return redirect(url_for('.games'))


@bp.route('/select_new_game_dates', methods=('GET', 'POST'))
@login_required
def select_new_game_dates():
    return render_template('/select_new_game_dates.html')


@bp.route('/select_included_games', methods=('GET', 'POST'))
@login_required
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

    return render_template('/select_included_games.html', startDate=start_date, endDate=end_date, d=d)
