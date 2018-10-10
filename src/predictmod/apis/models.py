from predictmod.app import app, api, mongo
from flask_restful import reqparse
import flask_restful as rest
import flask
import json
from predictmod.utils import MongoEncoder, get_datasets
from predictmod import db_helper
from predictmod.forecast_models import arima


def makeTrainModelOnCsvParser(for_update=False):
    parser = reqparse.RequestParser(trim=True)
    parser.add_argument('algorithm', required=True, nullable=False)
    parser.add_argument('dataset', required=True, nullable=False)
    parser.add_argument('train', nullable=False, type=float)
    parser.add_argument('test', nullable=False, type=float)
    return parser


class Models(rest.Resource):

    def get(self):
        # Fetch all models in db
        try:
            query_result = mongo.db.models.find()
        except Exception as e:
            return flask.jsonify(
                {
                    'status': '500',
                    'message': e.message
                }
            )
        encoder = MongoEncoder()
        try:
            docs = [json.loads(encoder.encode(doc)) for doc in query_result]
        except Exception as e:
            return flask.jsonify(
                {
                    'status': '500',
                    'message': 'Error Decoding Result: {}'.format(e.message)
                }
            )

        return flask.jsonify(docs)


class ActiveModel(rest.Resource):

    def get(self):
        try:
            active_model_id = db_helper.get_active_model()
            if active_model_id is None:
                return flask.jsonify(
                    {
                        'status': 404,
                        'message': "No trained model found, please activate a model \
                                    using /activate_model/<model_id>"
                    }
                )
            active_model = db_helper.get_model_by_id(active_model_id)
            return flask.jsonify(active_model)

        except Exception as e:
            return flask.jsonify(
                {
                    'status': '500',
                    'message': e.message
                }
            )


class ActivateModel(rest.Resource):

    def post(self, model_id):
        try:
            # Check model_id is valid
            model = db_helper.get_model_by_id(model_id)
            if model is None:
                return flask.jsonify(
                    {
                        'status': '500',
                        'message': 'Model with id {} is not saved'.format(model_id)
                    }
                )
            # Delete Current Model in use
            mongo.db.active_model.drop()
            # Attempt inserting model_id
            inserted = mongo.db.active_model.insert_one({'model_id': model_id})
            encoder = MongoEncoder()
            if inserted.inserted_id:
                return flask.jsonify(
                    {
                        'active_model': model_id,
                        'mongo_id': encoder.encode(inserted.inserted_id)
                    }
                )
        except Exception as e:
            return flask.jsonify(
                {
                    'status': '500',
                    'message': e.message
                }
            )


class TrainModelOnCsv(rest.Resource):

    def post(self):
        args = makeTrainModelOnCsvParser().parse_args()
        dataset_names = [f['name'] for f in get_datasets()]

        if not args.dataset or args.dataset not in dataset_names:
            return flask.jsonify(
                {
                    'status': '500',
                    'error': 'No such dataset'
                }
            )
        if args.algorithm == 'ARIMA':
            """Train model from instana data."""
            model = arima.ArimaModel(load_id=None, dataset=args.dataset)
            test, predictions = model.train_model_on_batch(model.training_data, model.testing_data)
            model_id = model.save_model(args.dataset)
            return flask.jsonify(db_helper.get_model_by_id(model_id))


api.add_resource(Models, '/models')
api.add_resource(ActivateModel, '/activate_model/<model_id>')
api.add_resource(ActiveModel, '/active_model')
api.add_resource(TrainModelOnCsv, '/train_model_csv')
