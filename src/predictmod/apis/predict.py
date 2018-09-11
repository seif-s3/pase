from predictmod.app import api
from predictmod.forecast_models.arima import ArimaModel
from predictmod import db_helper
from predictmod import utils
import flask_restful as rest
import flask
import datetime
import sys


class Predict(rest.Resource):

    def _train_csv(self, start_time, end_time):
        """Train model from instana data."""
        model = ArimaModel()
        test, predictions = model.train_model_on_batch(model.training_data, model.testing_data)

        to_forecast = 0
        start_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
        end_time = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ')
        temp_time = start_time
        while temp_time <= end_time:
            to_forecast += 1
            temp_time += datetime.timedelta(hours=1)

        # For now let's assume that the start_time will always be directly
        # after the last training data
        # predictions = model.forecast(to_forecast)
        ret = []
        t = start_time
        for p in predictions:
            ret.append({'time-stamp': t.strftime('%Y-%m-%dT%H:%M:%SZ'), 'requests': p[0]})
            t += datetime.timedelta(hours=1)
        return flask.jsonify({'id': 1, 'values': ret})

    def get(self):
        start_time = flask.request.args.get('start_time')
        end_time = flask.request.args.get('end_time')
        if start_time is None:
            return flask.jsonify({'error': 'Missing query param: start_time'})
        if end_time is None:
            return flask.jsonify({'error': 'Missing query param: end_time'})

        # TODO: Validate params are in expected format

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
            model = ArimaModel(load_id=active_model)
            model_attributes = db_helper.get_model_by_id(active_model)

            # K is the number of units (typically hours) we need to forecast
            # S is the number of units to skip from input_end to start_time
            K = utils.get_time_difference(model_attributes['input_end'], end_time)
            S = utils.get_time_difference(model_attributes['input_end'], start_time)

            if S > K:
                return flask.jsonify(
                    {
                        'status': 400,
                        'message': "Bad Request, start_time should be before end_time"
                    }
                )

            # start_time is the first timestamp to be sent in the response
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
            # end_time is the last timestamp to be send in the response
            end_time = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')

            predictions = model.forecast(K)

            # Discard first S predictions since they are not required in the response
            predictions_trimmed = predictions[S:]
            ret = []
            t = start_time
            for p in predictions_trimmed:
                ret.append({'time-stamp': t.strftime('%Y-%m-%dT%H:%M:%S'), 'requests': p})
                t += datetime.timedelta(hours=1)
            return flask.jsonify({'id': 1, 'values': ret})
        else:
            return flask.jsonify(
                {
                    'status': 404,
                    'message': "No trained model found, please activate a model \
                                using /activate_model/<model_id>"
                }
            )

api.add_resource(Predict, '/predict')
