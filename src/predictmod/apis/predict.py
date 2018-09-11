from predictmod.app import api
from predictmod.forecast_models.arima import ArimaModel
from predictmod import utils
import flask_restful as rest
import flask
import datetime
import sys

class Predict(rest.Resource):

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
        active_model = utils.get_active_model()
        print >> sys.stderr, "Active Model: {}".format(active_model)
        if active_model:
            model = ArimaModel(load_id=active_model)
            predictions = model.forecast(10)
            print >> sys.stderr, predictions
            ret = []
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
            end_time = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ')
            t = start_time
            for p in predictions:
                ret.append({'time-stamp': t.strftime('%Y-%m-%dT%H:%M:%SZ'), 'requests': p})
                t += datetime.timedelta(hours=1)
            return flask.jsonify({'id': 1, 'values': ret})
        else:
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

api.add_resource(Predict, '/predict')
