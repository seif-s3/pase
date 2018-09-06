import datetime
import flask
from flask_restful import Api
from flask_cors import CORS
from forecast_models.arima import ArimaModel


app = flask.Flask('predictmod')

CORS(app, origins=[r'.*localhost:5000$',
                   r'.*localhost:9999$'])

api = Api(app, catch_all_404s=True)


@app.route('/')
def hello_world():
    return 'prediction-module: OK'


import apis.predict
