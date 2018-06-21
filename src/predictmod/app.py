import flask
import datetime
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


@app.route('/predict')
def predict():
    model = ArimaModel()
    print len(model.series)
    test, predictions = model.train_model_on_batch(model.training_data, model.testing_data)
    ret = []
    t = datetime.datetime.strptime('2019-08-08T00:00:00Z', '%Y-%m-%dT%H:%M:%SZ')
    for p in predictions:
        ret.append({'time-stamp': t.strftime('%Y-%m-%dT%H:%M:%SZ'), 'requests': p[0]})
        t += datetime.timedelta(hours=1)
    return flask.jsonify({'id': 1, 'values': ret})
