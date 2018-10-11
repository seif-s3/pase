"""
Scheduled job that updates the current active_model.
This job will connect to the InfluxDB specified in the app config to fetch all readings after the
models training endtime.
Additionally, moedl will be retrained using more data and updated accordingly.
"""
import sys
import requests
from predictmod import db_helper


def job():
    active_model_id = db_helper.get_active_model()
    if not active_model_id:
        print >> sys.stdout, "Error: No Active model"
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
        'u': 'admin',
        'p': 'admin',
        'db': 'prometheus',
        'q': influx_query
    }
    response = requests.post("http://host.docker.internal:8086/query", data=payload)
    results = response.json()['results']
    if len(results) > 0:
        if 'series' in results[0] and len(results[0]['series']) >= 1:
            series = results[0]['series'][0]
            print >> sys.stderr, "FETCHED ", len(series['values']), " RECORDS!"
        else:
            print >> sys.stderr, "InfluxDB Query retunred no results!"

    return
