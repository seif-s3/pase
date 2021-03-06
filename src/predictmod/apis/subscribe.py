from predictmod.app import app, api, mongo
from flask_restful import reqparse
import flask_restful as rest
import flask
import json
import random
import sys
import requests
import datetime
from predictmod.utils import MongoEncoder
from predictmod import utils
from predictmod import db_helper


def makeSubscribeParser(for_update=False):
    parser = reqparse.RequestParser(trim=True)
    parser.add_argument('url', required=True, nullable=False)
    parser.add_argument('predictions_id', required=True, nullable=False)
    return parser


class Subscribe(rest.Resource):

    def post(self):
        args = makeSubscribeParser().parse_args()
        try:
            # Find predictions stored in DB ans make sure they're valid
            predictions = db_helper.get_predictions_by_id(args.predictions_id)
            if predictions is None:
                return flask.jsonify(
                    {
                        'status': '500',
                        'error': 'No predictions with id {} '.format(args.predictions_id)
                    }
                )

            if predictions['is_valid'] is False:
                return flask.jsonify(
                    {
                        'status': '500',
                        'error': 'Predictions with id {} were invalidated at {}'.format(
                            args.predictions_id, predictions['invalidated_at'])
                    }
                )

            # Save subscriber
            doc = {
                'url': args.url,
                'predictions': predictions,
                'registered_at': utils.utcnow(),
                'notified_at': []
            }

            inserted = mongo.db.subscribers.insert_one(doc)
            if inserted.inserted_id:
                return flask.jsonify(
                    {
                        'registered': True,
                        'id': str(inserted.inserted_id)
                    }
                )

        except Exception as e:
            return flask.jsonify(
                {
                    'status': '500',
                    'error': e.message
                }
            )


class TestSubscribe(rest.Resource):

    def get(self, id):
        subscriber = db_helper.get_subscriber_by_id(id)
        if subscriber is None:
            return flask.jsonify(
                {
                    'error': 'No subscriber with ID {}'.format(id)
                }
            )

        predictions = subscriber['predictions']
        thresholds = subscriber['thresholds']
        notified_at = subscriber['notified_at'] or []
        url = subscriber['url']

        mock = []
        ts = datetime.datetime.strptime(predictions['start_time'], '%Y-%m-%dT%H:%M:%SZ')
        for p, t in zip(predictions['values'], thresholds):
            mock.append(
                {
                    'timestamp': ts.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'value': p + (t * random.choice([1, 0])) + (random.random() * p)
                }
            )
            ts += datetime.timedelta(hours=1)

        response = {
            'id': 'newMockId',
            'values': mock,
            'start_time': predictions['start_time'],
            'end_time': predictions['end_time']

        }

        try:
            fail = False
            result = requests.post(url, json=response)
        except Exception as e:
            fail = True
            result = 'Error sending POST request to {}: {}'.format(url, e.message)

        if fail:
            mock_resonse = {
                'status': 'Fail',
                'result': result
            }
        else:
            mock_resonse = {
                'url': url,
                'json': response,
                'message': 'Attempted',
                'result': result.text
            }
            mongo.db.subscribers.update_one(
                {'id': id},
                {'$set': {'notified_at': notified_at + [utils.utcnow()]}}
            )
        return flask.jsonify(mock_resonse)


api.add_resource(Subscribe, '/subscribe')
api.add_resource(TestSubscribe, '/test_sub/<id>')
