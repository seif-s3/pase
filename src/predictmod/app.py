import atexit
import os
import datetime
import flask
import sys
from flask_pymongo import PyMongo
from flask_restful import Api
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread


scheduler = BackgroundScheduler(coalesce=True, timezone='utc')
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


app = flask.Flask('predictmod')
app.secret_key = os.urandom(16)

CORS(app, origins=[r'.*localhost:5000$',
                   r'.*localhost:9999$'])


app.config['UPLOAD_FOLDER'] = '/datasets'

# MongoDB Initialization
app.config['MONGODB_HOST'] = os.environ.get('MONGODB_HOST', 'localhost')
app.config['MONGODB_PORT'] = os.environ.get('MONGODB_PORT', 27017)
app.config['MONGO_URI'] = os.environ.get(
    'MONGODB_URI', 'mongodb://{user}:{pwd}@mongodb:27017/pase'.format(user='root', pwd='example'))

mongo = PyMongo(app)

api = Api(app, catch_all_404s=True)


# 'interval' jobs run after a certain tim
# 'cron' jobs run at a specified hour/minute
@scheduler.scheduled_job('interval', minutes=1)
def update_model():
    try:
        print >> sys.stderr, "Triggering update_model job: ", datetime.datetime.now()
        from predictmod.cron import update_model
        update_model.job()
    except Exception as e:
        print >> sys.stderr, "Exception caught while running job!"
        print >> sys.stderr, e


@app.route('/')
def healthcheck():
    return flask.jsonify(
        {
            'prediction-module': 'OK',
            'mongodb': 'mongodb://mongodb:27017/pase'
        }
    )


import apis.predict
import apis.models
import apis.datasets
import apis.subscribe
