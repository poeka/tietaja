import os

from flask import (Flask, g)
from flask_bootstrap import Bootstrap
from .database import db
from .views import test
from .tasks import task
#from apscheduler.schedulers.background import BackgroundScheduler
from tietaja.database.db import get_db
from flask_apscheduler import APScheduler


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    Bootstrap(app)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    db.init_app(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.register_blueprint(test.bp)
    app.register_blueprint(task.bp)

    #scheduler = BackgroundScheduler()
    # scheduler.start()
    #scheduler.add_job(task.checkResults(), 'interval', seconds=10)

    #scheduler.add_job(task.checkResults, 'interval', seconds=10)

    return app
