import os
import datetime
import flask
from flask_pymongo import PyMongo
from flask_restful import Api
from flask_cors import CORS


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
