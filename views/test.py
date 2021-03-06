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

        print(request.form.getlist('selected'))

        try:
            selected = request.form.getlist('selected')
            gameid = randint(10000, 99999)
            user_id = session['user_id']

            db = get_db()
            db.execute(
                'INSERT INTO game (game_id, creator, owner_bet, lock_state) VALUES (?, ?, ?, ?)',
                (gameid, user_id, 0, 0)
            )

            for matchId in selected:

                uri = 'https://statsapi.web.nhl.com/api/v1/game/' + \
                    str(matchId) + '/linescore'

                try:
                    uResponse = requests.get(uri)
                except requests.ConnectionError:
                    return "Connection Error"
                Jresponse = uResponse.text
                gameInfo = json.loads(Jresponse)

                away = gameInfo['teams']['away']['team']['name']
                home = gameInfo['teams']['home']['team']['name']

                db.execute(
                    'INSERT INTO match (match_id, game_id, home_team, away_team, bettable, result, finished) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (matchId, gameid, home, away, 1, 0, 0,)
                )

            db.commit()
            print('done')
            return redirect(url_for('.games'))

        except:
            print('error')

            return redirect(url_for('.home'))

    else:

        browser = request.user_agent.browser  # just for testing
        print(browser)

        user_id = session['user_id']

        try:
            gameId = request.args['gameId']
        except:
            print('haloo1')
            return redirect(url_for('.games'))

        db = get_db()

        if not db.execute('SELECT * FROM game WHERE game_id = ?',
                          (gameId,)).fetchone():
            return redirect(url_for('.games'))

        games = db.execute('SELECT * FROM match WHERE game_id = ?',
                           (gameId,)).fetchall()

        print("Get game details")

        # Check if bet is already set

        gameToCheck = db.execute('SELECT * FROM game WHERE game_id = ?',
                                 (gameId,)).fetchone()

        lock_state = gameToCheck['lock_state']  # redundant, can be removed
        print('lock_state (game): '+str(lock_state))

        bet = 0
        if gameToCheck['creator'] == session['user_id']:
            bet = gameToCheck['owner_bet']
            owned = 1
        else:
            gameToCheck = db.execute('SELECT * FROM joined WHERE game_id = ? AND player = ?',
                                     (gameId, session['user_id'])).fetchone()
            bet = gameToCheck['bet']
            owned = 0

        selected = []

        game_finished = 1  # This is used to find out if all matches in one game are finished

        for game in games:

            result = game['result']

            if result == "0":
                result = "Game not yet started"
                game_finished = 0

                if game['bettable'] == 0 and game['finished'] == 0:
                    result = "Game is ongoing"

            prediction = ""
            if bet == 1:

                prediction_binary = db.execute('SELECT prediction FROM bet WHERE game_id = ? AND match_id = ? AND player = ?',
                                               (gameId, game['match_id'], user_id,)).fetchone()

                print(prediction_binary)
                if prediction_binary['prediction'] == 0:
                    prediction = "0"
                elif prediction_binary['prediction'] == 1:
                    prediction = "1"
                elif prediction_binary['prediction'] == 3:
                    prediction = "X"
                elif prediction_binary['prediction'] == 2:
                    prediction = "2"

                # TODO: save results to db match table in a smart way

                selected.append({'game_id': gameId, 'match_id': game['match_id'], 'away': game['away_team'],
                                 'home': game['home_team'], 'prediction': prediction, 'result': result, 'bettable': str(game['bettable'])})

            else:
                selected.append(
                    {'game_id': gameId, 'match_id': game['match_id'], 'away': game['away_team'], 'home': game['home_team'], 'result': result, 'bettable': str(game['bettable'])})

        # Get players and results

        players = db.execute('SELECT * FROM joined WHERE game_id = ?',
                             (gameId,)).fetchall()

        number_of_matches = len(db.execute('SELECT * FROM match WHERE game_id = ?',
                                           (gameId,)).fetchall())

        joined_users = {}

        creator = db.execute('SELECT * FROM game WHERE game_id = ?',
                             (gameId,)).fetchone()['creator']

        owner = db.execute('SELECT * FROM user WHERE id = ?',
                           (creator,)).fetchone()['username']  # The game owner

        bets = db.execute('SELECT * FROM bet WHERE game_id = ? AND player = ?',
                          (gameId, creator,)).fetchall()

        bet_results = 0
        match_result = 0

        for bet in bets:

            try:
                match_result = db.execute('SELECT * FROM match WHERE match_id = ?',
                                          (str(bet['match_id']),)).fetchone()['result']

            except:
                continue

            if str(match_result) == "0" or int(bet['prediction']) == 0:
                continue

            elif str(match_result) == "1" and int(bet['prediction']) == 1:
                bet_results += 1

            elif str(match_result) == "2" and int(bet['prediction']) == 2:
                bet_results += 1

            elif match_result == "X" and bet['prediction'] == 3:
                bet_results += 1

        joined_users[owner] = str(bet_results) + '/' + str(number_of_matches)

        for player in players:

            user = db.execute('SELECT * FROM user WHERE id = ?',
                              (int(player['player']),)).fetchone()['username']

            bets = db.execute('SELECT * FROM bet WHERE game_id = ? AND player = ?',
                              (gameId, int(player['player']),)).fetchall()

            bet_results = 0
            match_result = 0

            for bet in bets:

                try:
                    match_result = db.execute('SELECT * FROM match WHERE match_id= ?',
                                              (str(bet['match_id']),)).fetchone()['result']

                except:
                    continue

                if str(match_result) == "0" or int(bet['prediction']) == 0:
                    continue

                elif str(match_result) == "1" and int(bet['prediction']) == 1:
                    bet_results += 1

                elif str(match_result) == "2" and int(bet['prediction']) == 2:
                    bet_results += 1

                elif str(match_result) == "X" and int(bet['prediction']) == 3:
                    bet_results += 1

            joined_users[user] = str(bet_results) + \
                '/' + str(number_of_matches)

        return render_template('game.html', games=selected, owned=owned, finished=game_finished, players=joined_users)


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
        'INSERT INTO joined (game_id, player, bet) VALUES (?, ?, ?)',
        (gameId, session['user_id'], 0)
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

    for date in data['dates']:
        for game in date['games']:
            gameId = game['gamePk']

            # Check that the game is not yet started/finished
            if game['status']['detailedState'] != 'Scheduled':
                continue

            away = game['teams']['away']['team']['name']
            home = game['teams']['home']['team']['name']
            d[gameId] = [home, away]

    return render_template('/select_included_games.html', startDate=start_date, endDate=end_date, d=d)


@bp.route('/set_predictions',  methods=('GET', 'POST'))
@login_required
def set_predictions():

    try:
        print(request.form)
        print(request.form.getlist('match_id'))
        print(request.form['game_id'])

        gameId = request.form['game_id']
        matches = request.form.getlist('match_id')
        user_id = session['user_id']

    except:
        return redirect(url_for('.games'))

    db = get_db()

    for match in matches:
        try:
            prediction = request.form[match]
        except:
            prediction = 0  # 0 means that no prediction is set.

        betPlaced = 0
        betPlaced = db.execute('SELECT * FROM bet WHERE game_id = ? AND player = ? AND match_id = ?',
                               (gameId, user_id, match,)).fetchone()

        if betPlaced:

            checkBettable = db.execute('SELECT * FROM match WHERE match_id = ?',
                                       (match,)).fetchone()

            if not checkBettable['bettable']:
                continue

            db.execute(
                'UPDATE bet SET prediction = ? WHERE game_id = ? AND player = ? AND match_id = ?',
                (prediction, gameId, user_id, match,)
            )

        else:
            db.execute(
                'INSERT INTO bet (game_id, match_id, player, prediction) VALUES (?, ?, ?, ?)',
                (gameId, match, user_id, prediction)
            )

    db.commit()

    bet = 1

    # Check if game is owned

    gameToCheck = db.execute('SELECT * FROM game WHERE game_id = ?',
                             (gameId,)).fetchone()

    if gameToCheck['creator'] == user_id:
        print(user_id)
        db.execute(
            'UPDATE game SET owner_bet = ? WHERE game_id = ? ',
            (1, gameId)
        )
        db.commit()
    else:
        db.execute(
            'UPDATE joined SET bet = ? WHERE game_id = ? AND player = ?',
            (bet, gameId, user_id,)
        )
        db.commit()

    return redirect(url_for('.game', gameId=gameId))


@bp.route('/toggle_state', methods=('GET', 'POST'))
@login_required
def toggle_state():

    try:
        print(request.form)
        print(request.form['game_id'])

        gameId = request.form['game_id']
        lock_state = int(request.form['lock_state'])

    except:
        return redirect(url_for('.games'))

    print('lock_state: ' + str(lock_state))

    if lock_state == 0:
        lock_state = 1
    else:
        lock_state = 0

    db = get_db()

    db.execute(
        'UPDATE game SET lock_state = ? WHERE game_id = ? ',
        (lock_state, gameId)
    )
    db.commit()

    return redirect(url_for('.game', gameId=gameId))
