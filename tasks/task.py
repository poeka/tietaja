import functools
import requests
import json
from tietaja.database.db import get_db
from flask_apscheduler import APScheduler


from flask import (
    Blueprint, Flask, g, render_template, request, session, jsonify
)


bp = Blueprint('task', __name__)


app = Flask(__name__)

# app.config.from_object(Config())

app.config.from_object(app)

scheduler = APScheduler()


@scheduler.task('interval', id='getResults', seconds=30, misfire_grace_time=900)
def getResults():

    print("Fetching results")

    app = Flask(__name__)

    with app.app_context():

        db = get_db()

        games = db.execute(
            'SELECT * FROM match WHERE bettable = ? AND finished = ?', (0, 0)).fetchall()

        for game in games:

            uri = 'https://statsapi.web.nhl.com/api/v1/game/' + \
                str(game['match_id']) + '/linescore'

            try:
                uResponse = requests.get(uri)
            except requests.ConnectionError:
                return "Connection Error"

            Jresponse = uResponse.text
            gameInfo = json.loads(Jresponse)

            print('currentperiod: ' + str(gameInfo['currentPeriod']))

            if int(gameInfo['currentPeriod']) == 3 or int(gameInfo['currentPeriod']) == 4 or int(gameInfo['currentPeriod']) == 5:

                if gameInfo['currentPeriodTimeRemaining'] == "Final":

                    away_score = gameInfo['teams']['away']['goals']
                    home_score = gameInfo['teams']['home']['goals']

                    if int(gameInfo['currentPeriod']) == 4 or int(gameInfo['currentPeriod']) == 5:
                        result = "X"
                    elif home_score > away_score:
                        result = "1"
                    elif home_score < away_score:
                        result = "2"

                    db.execute('UPDATE match SET finished = ? WHERE match_id= ?',
                               (1, game['match_id']))

                    db.execute('UPDATE match SET result = ? WHERE match_id= ?',
                               (result, game['match_id']))

                    db.commit()

        return


@scheduler.task('interval', id='lockGames', seconds=15, misfire_grace_time=900)
def lockGames():

    print("Locking games if needed")

    app = Flask(__name__)

    with app.app_context():

        db = get_db()

        games = db.execute(
            'SELECT * FROM match WHERE bettable = ?', (1,)).fetchall()

        for game in games:

            uri = 'https://statsapi.web.nhl.com/api/v1/game/' + \
                str(game['match_id']) + '/linescore'

            try:
                uResponse = requests.get(uri)
            except requests.ConnectionError:
                return "Connection Error"

            Jresponse = uResponse.text
            gameInfo = json.loads(Jresponse)

            if int(gameInfo['currentPeriod']) != 0:

                db.execute('UPDATE match SET bettable= ? WHERE match_id= ?',
                           (0, game['match_id']))

                db.commit()

        return


scheduler.init_app(app)
scheduler.start()
