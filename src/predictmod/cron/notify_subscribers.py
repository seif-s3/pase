"""
Scheduled job that notifies subscribers of changes in the predictions sent before.

This job will use the active model to generate new predictions for the same timeframe.
If significant drift is detected, old predictions will be invalidated and new predictions will be
sent.
Assumption here is that the active_model is always up to date since it periodically queries InfluxDB
for new readings.
"""
import sys
import requests
import datetime
import math
from predictmod import db_helper
from predictmod import utils
from predictmod.forecast_models.arima import ArimaModel


def job():
    subscribers = db_helper.get_all_subscribers()
    if len(subscribers) == 0:
        print >> sys.stderr, "No subscribers to notify"
        return

    for s in subscribers:
        print >> sys.stderr, "Processing Subcscriber", s['_id']
        notify_url = s['url']
        predictions = s['predictions']

        start_time = predictions['start_time']
        end_time = predictions['end_time']
        old_predictions = predictions['values']

        # Use active model to predict same range.
        active_model = db_helper.get_active_model()
        print >> sys.stderr, "Using Active Model: {}".format(active_model)
        if active_model:
            model = ArimaModel(load=True, model_id=active_model)
            model_attributes = db_helper.get_model_by_id(active_model)
            K = utils.get_time_difference(model_attributes['input_end'], end_time) + 1
            S = utils.get_time_difference(model_attributes['input_end'], start_time)

            if S > K:
                print >> sys.stderr, "Bad Request, start_time should be before end_time"
                return

            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
            end_time = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ')

            forecasted = model.forecast(K)
            # Discard first S predictions since they are not required in the response
            new_predictions = forecasted[S:]

            # Prepare JSON to be sent in case difference is significant
            new_json = []
            new_values = []
            t = start_time
            for p in new_predictions:
                new_values.append(p)
                new_json.append({'timestamp': t.strftime('%Y-%m-%dT%H:%M:%SZ'), 'requests': p})
                t += datetime.timedelta(hours=1)

            distance = math.sqrt(
                sum(
                    [(old - new)**2 for old, new in zip(old_predictions, new_predictions)]
                )
            )
            print >> sys.stderr, "Difference in predictions: ", distance
            # TODO: Change threshold value!!
            if distance >= 10:
                # Invalidate old predictions
                db_helper.invalidate_predictions(predictions['_id'])
                # Save new predictions:
                to_save = {
                    'start_time': start_time,
                    'end_time': end_time,
                    'values': new_values,
                    'granularity': 'hour',
                    'is_valid': True,
                    'generated_at': utils.utcnow(),
                    'model': active_model
                }

                new_predictions_id = db_helper.save_predictions(to_save)
                response = {
                    'id': new_predictions_id,
                    'values': new_json,
                    'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

                }
                # Notify subscriber
                try:
                    fail = False
                    result = requests.post(notify_url, json=response)
                except Exception as e:
                    fail = True
                    result = 'Error sending POST request to {}: {}'.format(notify_url, e.message)

                print >> sys.stderr, "Notified {}".format(notify_url)
                print >> sys.stderr, "Result {}".format(result)

                if not fail:
                    # Update subscriber
                    db_helper.update_subscriber_predictions(s, new_predictions_id)

        else:
            print >> sys.stderr, """
                No trained model found, please activate a model using /activate_model/<model_id>"""
