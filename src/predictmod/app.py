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


@app.route('/predict')
def predict():
    start_time = flask.request.args.get('start_time')
    end_time = flask.request.args.get('end_time')
    if start_time is None:
        return flask.jsonify({'error': 'Missing query param: start_time'})
    if end_time is None:
        return flask.jsonify({'error': 'Missing query param: end_time'})

    # TODO: Validate params are in expected format

    # Granularity by default is 1 hour
    model = ArimaModel()
    test, predictions = model.train_model_on_batch(model.training_data, model.testing_data)

    to_forecast = 0
    start_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ')
    temp_time = start_time
    while temp_time <= end_time:
        to_forecast += 1
        temp_time += datetime.timedelta(hours=1)

    # For now let's assume that the start_time will always be directly after the last training data
    # predictions = model.forecast(to_forecast)
    ret = []
    t = start_time
    for p in predictions:
        ret.append({'time-stamp': t.strftime('%Y-%m-%dT%H:%M:%SZ'), 'requests': p[0]})
        t += datetime.timedelta(hours=1)
    return flask.jsonify({'id': 1, 'values': ret})
