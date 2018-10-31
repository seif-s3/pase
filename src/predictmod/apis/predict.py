from predictmod.app import api, mongo
from predictmod.forecast_models.arima import ArimaModel
from predictmod.forecast_models.autoarima import AutoArimaModel
from predictmod import db_helper
from predictmod import utils
import flask_restful as rest
import flask
import datetime
import sys
import pytz
import numpy as np


def validate_bounds(start, end):
    """
    Function that validates start and end timestamps are valid.

    A valid pair of timestamps for predictions must fulfill the following conditions:
    1- Format matches %Y-%m-%dT%H:%M:%SZ
    2- end_time > start_time
    3- start_time > now : We want to forecast the future
    """
    print >> sys.stderr, start, end
    try:
        start = pytz.UTC.localize(datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%SZ'))
        end = pytz.UTC.localize(datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%SZ'))

    except:
        return False, "Formats don't match %Y-%m-%dT%H:%M:%SZ"

    if start > end:
        return False, "start_time should be before end_time"

    if start <= utils.utcnow():
        return False, "start_time must be in the future"

    return True, None


class Predict(rest.Resource):

    def get(self):
        try:
            start_time = flask.request.args.get('start_time')
            end_time = flask.request.args.get('end_time')
            if start_time is None:
                return flask.jsonify({'error': 'Missing query param: start_time'})
            if end_time is None:
                return flask.jsonify({'error': 'Missing query param: end_time'})

            valid, err = validate_bounds(start_time, end_time)
            if not valid:
                return flask.jsonify(
                    {
                        'status': 400,
                        'error': err
                    }
                )
            # Granularity by default is 1 hour
            '''
            Steps:
            1- Check if there's a saved model
            2- Load saved model and do predictions
            3- If no model is saved -> create new model, train and predict.
            '''
            active_model = db_helper.get_active_model()
            print >> sys.stderr, "Active Model: {}".format(active_model)
            if active_model:
                model_attributes = db_helper.get_model_by_id(active_model)

                if model_attributes['algorithm'] == 'ARIMA':
                    model = ArimaModel(load=True, model_id=active_model)
                elif model_attributes['algorithm'] == 'AutoARIMA':
                    model = AutoArimaModel(load=True, model_id=active_model)
                else:
                    return flask.jsonify(
                        {
                            'status': 500,
                            'message': 'Unknown model algorithm'
                        }
                    )
                # K is the number of units (typically hours) we need to forecast
                # K + 1 to include the start timestamp (consider it 0 indexed)
                # S is the number of units to skip from input_end to start_time

                K = utils.get_time_difference(model_attributes['input_end'], end_time) + 1
                S = utils.get_time_difference(model_attributes['input_end'], start_time)

                if S > K:
                    return flask.jsonify(
                        {
                            'status': 400,
                            'message': "Bad Request, start_time should be before end_time"
                        }
                    )

                # start_time is the first timestamp to be sent in the response
                start_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
                # end_time is the last timestamp to be send in the response
                end_time = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ')

                # Check wheather we already have predictions for the same timeframe using the same
                # model.
                found_predictions = db_helper.find_predictions(
                    start_time=start_time, end_time=end_time,
                    granularity='hour', model=str(active_model), is_valid=True
                )

                if found_predictions is None or (
                        found_predictions['generated_at'] < model_attributes['acquisition_time']
                ):
                    # Model has been retrained using newer input, we should generate new preditcions
                    if found_predictions:
                        db_helper.invalidate_predictions(found_predictions['_id'])
                    predictions = model.forecast(K)

                    # Discard first S predictions since they are not required in the response
                    predictions_trimmed = predictions[S:]
                    ret = []
                    arr = []
                    t = start_time
                    for p in predictions_trimmed:
                        arr.append(p)
                        ret.append({'timestamp': t.strftime('%Y-%m-%dT%H:%M:%SZ'), 'requests': p})
                        t += datetime.timedelta(hours=1)

                    to_save = {
                        'start_time': start_time,
                        'end_time': end_time,
                        'values': arr,
                        'granularity': 'hour',
                        'is_valid': True,
                        'generated_at': utils.utcnow(),
                        'model': active_model
                    }
                    inserted = mongo.db.predictions.insert_one(to_save)
                    if inserted.inserted_id:
                        return flask.jsonify(
                            {
                                'id': str(inserted.inserted_id),
                                'values': ret,
                                'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                'model': str(active_model),
                                'generated_at': utils.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                            }
                        )
                else:
                    # Predictions we have are still valid, no need to generate new ones
                    print >> sys.stderr, "Valid Predictions: ", found_predictions['generated_at']
                    # Reformat predictions to expected response format
                    t = start_time
                    ret = []
                    for p in found_predictions['values']:
                        ret.append({'timestamp': t.strftime('%Y-%m-%dT%H:%M:%SZ'), 'requests': p})
                        t += datetime.timedelta(hours=1)
                    found_predictions['values'] = ret
                    found_predictions['id'] = found_predictions['_id']
                    # Hacky way of reformatting datetime
                    found_predictions['generated_at'] = found_predictions['generated_at'][:-8] + "Z"
                    del found_predictions['_id']
                    del found_predictions['granularity']
                    del found_predictions['is_valid']
                    return flask.jsonify(found_predictions)
            else:
                return flask.jsonify(
                    {
                        'status': 404,
                        'message': "No trained model found, please activate a model \
                                    using /activate_model/<model_id>"
                    }
                )
        except Exception as e:
            import traceback
            traceback.print_exc(file=sys.stderr)
            return flask.jsonify(
                {
                    'error': e.message,
                }
            )

api.add_resource(Predict, '/predict')
