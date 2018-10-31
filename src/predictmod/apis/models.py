from predictmod.app import app, api, mongo, scheduler
from flask_restful import reqparse
import flask_restful as rest
import flask
import json
import shutil
import threading
import sys
from predictmod.utils import MongoEncoder, get_datasets, utcnow
from predictmod import db_helper
from predictmod.forecast_models import arima, autoarima


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
                # When activating a new model, we need to create a copy of the training dataset to
                # be augmented with future data that is scraped automatically.
                model_attributes = db_helper.get_model_by_id(model_id)
                dataset = model_attributes['metadata']['dataset']
                if model_attributes['input_source'] == 'csv':
                    # If model was trained using a csv file
                    print >> sys.stderr, "Copying:", dataset, "to", '/model_inputs/{}.csv'.format(
                        model_id)
                    shutil.copyfile(
                        '/datasets/{}'.format(dataset),
                        '/model_inputs/{}.csv'.format(model_id)
                    )

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


def backgroundAutoArima(task_id, dataset):
    # AutoArima takes too long to train. We train on a separate thread and return the result
    db_helper.update_task_by_id(task_id, status='running', started_at=utcnow())
    model = autoarima.AutoArimaModel(dataset=dataset)
    model.train_model(model.training_data, model.testing_data)
    model_id = model.save_model(dataset)
    db_helper.update_task_by_id(
        task_id, status='finished', model_id=model_id, completed_at=utcnow())


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
            model = arima.ArimaModel(dataset=args.dataset)
            test, predictions = model.train_model(model.training_data, model.testing_data)
            model_id = model.save_model(args.dataset)
            return flask.jsonify(db_helper.get_model_by_id(model_id))
        elif args.algorithm == 'AutoARIMA':
            # AutoArima takes too long to train. We train on a separate thread and return the result
            inserted_task = mongo.db.tasks.insert_one(
                {'algorithm': 'AutoARIMA', 'status': 'pending'})
            task_id = str(inserted_task.inserted_id)

            # Monkey Patch: Use scheduler executors to run job then remove it
            scheduler.add_job(backgroundAutoArima, args=(task_id, args.dataset))
            print >> sys.stderr, "Scheduled job"
            return flask.jsonify(
                {
                    'message': 'Training started. Check /training?task_id=<> for status',
                    'task_id': task_id
                }
            )
            # model.train_model(model.training_data, model.testing_data)
            # model_id = model.save_model(args.dataset)


class TrainingStatus(rest.Resource):
    def get(self):
        task_id = flask.request.args.get('task_id')
        return flask.jsonify(db_helper.get_task_by_id(task_id))


api.add_resource(Models, '/models')
api.add_resource(ActivateModel, '/activate_model/<model_id>')
api.add_resource(ActiveModel, '/active_model')
api.add_resource(TrainModelOnCsv, '/train_model_csv')
api.add_resource(TrainingStatus, '/training')
