"""
Scheduled job that retrains the current active_model if new data is fetched from InfluxDB.

This job will connect to the InfluxDB specified in the app config to fetch all readings after the
models training endtime.
Additionally, moedl will be retrained using more data and updated accordingly.
"""
import sys
import requests
import datetime
from predictmod import db_helper
from predictmod.app import app
from predictmod.forecast_models.arima import ArimaModel
from predictmod.forecast_models.autoarima import AutoArimaModel
from predictmod.cron import notify_subscribers


def start_notify_subscribers():
    try:
        print >> sys.stderr, "Triggering notify_subscribers job: ", datetime.datetime.now()
        notify_subscribers.job()
    except Exception as e:
        print >> sys.stderr, "Exception caught while running notify_subscribers job!"
        print >> sys.stderr, e


def reformat_influx_series(series):
    ret = []
    for v in series['values']:
        ret.append({'timestamp': v[0], 'value': v[1]})
    return ret


def append_dataset(model_id, new_data):
    # The /model_inputs directory will always contain all data used to train a specific model.
    # Everytime we fetch new data from Influx, we append the training data file.
    # Open model file in append mode.
    f = open('/model_inputs/{}.csv'.format(model_id), 'a')
    for point in new_data:
        f.write("{},{}\n".format(point['timestamp'], point['value']))
    f.close()


def job():
    INFLUX_HOST = app.config.get('INFLUX_HOST', 'http://host.docker.internal:8086')
    INFLUX_DB = app.config.get('INFLUX_DB', 'prometheus')
    INFLUX_USER = app.config.get('INFLUX_USER', 'admin')
    INFLUX_PASS = app.config.get('INFLUX_PASS', 'admin')

    active_model_id = db_helper.get_active_model()
    if not active_model_id:
        print >> sys.stderr, "Error: No Active model"
        return

    model = db_helper.get_model_by_id(active_model_id)
    input_end = model['input_end']

    # TODO change granularity dynamically here
    granularity = '1h'

    influx_query = """
        SELECT derivative(value, {granularity}) AS value
        FROM (
            SELECT MAX(value) AS value
            FROM request_count
            WHERE time > '{end_time}'
            GROUP BY time({granularity})
        )
    """.format(granularity=granularity, end_time=input_end)
    print >> sys.stderr, influx_query
    payload = {
        'u': INFLUX_USER,
        'p': INFLUX_PASS,
        'db': INFLUX_DB,
        'q': influx_query
    }
    response = requests.post(INFLUX_HOST + "/query", data=payload)
    results = response.json()['results']
    if len(results) > 0:
        if 'series' in results[0] and len(results[0]['series']) >= 1:
            series = results[0]['series'][0]
            print >> sys.stderr, "FETCHED ", len(series['values']), " RECORDS!"
            new_data = reformat_influx_series(series)
            # Save new training data to CSV
            append_dataset(active_model_id, new_data)

            if model['algorithm'] == 'ARIMA':
                model = ArimaModel(retrain=True, model_id=active_model_id)
            elif model['algorithm'] == 'AutoARIMA':
                new_values = []
                for v in series['values']:
                    new_values.append(v[1])
                model = AutoArimaModel(
                    retrain=True, model_id=active_model_id, new_data=new_values)

            model.pklize(active_model_id)
            db_helper.update_model_input(active_model_id, new_data[-1]['timestamp'])

            # If model is retrained, let's notify subscribers
            start_notify_subscribers()
        else:
            print >> sys.stderr, "InfluxDB Query retunred no results!"
    return
