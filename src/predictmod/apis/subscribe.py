from predictmod.app import app, api, mongo
from flask_restful import reqparse
import flask_restful as rest
import flask
import json
import random
import sys
from predictmod.utils import MongoEncoder
from predictmod import utils
from predictmod import db_helper


def makeSubscribeParser(for_update=False):
    parser = reqparse.RequestParser(trim=True)
    parser.add_argument('url', required=True, nullable=False)
    parser.add_argument('thresholds', action='append', required=True, nullable=False)
    parser.add_argument('predictions_id', required=True, nullable=False)
    return parser


class Subscribe(rest.Resource):

    def post(self):
        args = makeSubscribeParser().parse_args()
        try:
            # Find predictions stored in DB ans make sure they're valid
            qr = mongo.db.predictions.find_one({'id': args.predictions_id})
            if qr is None:
                return flask.jsonify(
                    {
                        'status': '500',
                        'error': 'No predictions with id {} '.format(args.predictions_id)
                    }
                )
            encoder = MongoEncoder()
            predictions = json.loads(encoder.encode(qr))
            if predictions['is_valid'] is False:
                return flask.jsonify(
                    {
                        'status': '500',
                        'error': 'Predictions with id {} were invalidated at {}'.format(
                            args.predictions_id, predictions['invalidated_at'])
                    }
                )

            # Check thresholds are equal in length to predictions
            if len(predictions['values']) != len(args.thresholds):
                return flask.jsonify(
                    {
                        'status': '500',
                        'error':
                            '''Thresholds length do not match predictions.
                            Got {} expected {}'''.format(
                                len(args.thresholds), len(predictions['values']))
                    }
                )

            # Save subscriber
            sub_id = utils.generate_uuid()
            doc = {
                'id': sub_id,
                'url': args.url,
                'predictions': predictions['values'],
                'thresholds': args.thresholds,
                'registered_at': utils.utcnow(),
                'notified_at': None
            }
            inserted = mongo.db.subscribers.insert_one(doc)
            encoder = MongoEncoder()
            if inserted.inserted_id:
                in_db = db_helper.get_subscriber_by_id(sub_id)
                return flask.jsonify(
                    {
                        'registered': True,
                        'id': in_db['id']
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
        try:
            subscriber = db_helper.get_subscriber_by_id(id)
            predictions = subscriber['predictions']
            thresholds = subscriber['thresholds']

            mock = []
            for p, t in zip(predictions, thresholds):
                mock.append(p + (t * random.choice([1, 0]) + (random.random() * p)))

            return flask.jsonify(
                {
                    'id': utils.generate_uuid(),
                    'values': mock
                }
            )
        except Exception as e:
            return flask.jsonify(
                {
                    'error': e.message
                }
            )


api.add_resource(Subscribe, '/subscribe')
api.add_resource(TestSubscribe, '/test_sub/<id>')
