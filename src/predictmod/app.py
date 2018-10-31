import atexit
import os
import datetime
import flask
import sys
from flask_pymongo import PyMongo
from flask_restful import Api
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler


scheduler = BackgroundScheduler(coalesce=True, timezone='utc')
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


app = flask.Flask('predictmod')
app.secret_key = os.urandom(16)

CORS(app, origins=[r'.*localhost:5000$',
                   r'.*localhost:9999$'])


app.config['UPLOAD_FOLDER'] = '/datasets'

# MongoDB Initialization
app.config['MONGODB_HOST'] = os.environ.get('MONGODB_HOST', 'mongodb')
app.config['MONGODB_PORT'] = os.environ.get('MONGODB_PORT', 27017)
app.config['MONGODB_USER'] = os.environ.get('MONGODB_USER', 'root')
app.config['MONGODB_PASS'] = os.environ.get('MONGODB_PASS', 'example')
app.config['MONGODB_DB'] = os.environ.get('MONGODB_DB', 'pase')

app.config['MONGO_URI'] = os.environ.get(
    'MONGODB_URI', 'mongodb://{user}:{pwd}@{host}:{port}/{db}'.format(
        user=app.config['MONGODB_USER'],
        pwd=app.config['MONGODB_PASS'],
        host=app.config['MONGODB_HOST'],
        port=app.config['MONGODB_PORT'],
        db=app.config['MONGODB_DB']
    )
)

mongo = PyMongo(app)

# Influx DB Config
# This InfluxDB will be the source of new readings
app.config['INFLUX_HOST'] = os.environ.get('INFLUX_URL', 'http://host.docker.internal:8086')
app.config['INFLUX_DB'] = os.environ.get('INFLUX_DB', 'prometheus')
app.config['INFLUX_USER'] = os.environ.get('INFLUX_USER', 'admin')
app.config['INFLUX_PASS'] = os.environ.get('INFLUX_PASS', 'admin')

api = Api(app, catch_all_404s=True)


# ===================================== CRON JOBS ================================================ #
# 'interval' jobs run after a certain tim
# 'cron' jobs run at a specified hour/minute
def update_model():
    try:
        print >> sys.stderr, "Triggering update_model job: ", datetime.datetime.now()
        from predictmod.cron import update_model
        update_model.job()
    except Exception as e:
        print >> sys.stderr, "Exception caught while running update_model job!"
        print >> sys.stderr, e


update_model_job = scheduler.add_job(update_model, 'interval', minutes=1)

# ===================================== Endpoints ================================================ #
@app.route('/')
def healthcheck():
    return flask.jsonify(
        {
            'prediction-module': 'OK',
            'mongodb': app.config['MONGODB_DB'],
            'mongo_host': app.config['MONGODB_HOST'],
            'mongo_port': app.config['MONGODB_PORT'],
            'influx_host': app.config['INFLUX_HOST'],
            'influx_db': app.config['INFLUX_DB'],
            'influx_user': app.config['INFLUX_USER'],
            'influx_pass': app.config['INFLUX_PASS']
        }
    )


import apis.predict
import apis.models
import apis.datasets
import apis.subscribe
import apis.config