from predictmod.app import app, api, mongo
import flask_restful as rest
import flask
import json
from predictmod.utils import MongoEncoder


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


class ActivateModel(rest.Resource):

    def post(self, model_id):
        try:
            # Check model_id is valid
            found = mongo.db.models.find_one({'id': model_id})
            if found is None:
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


api.add_resource(Models, '/models')
api.add_resource(ActivateModel, '/activate_model/<model_id>')
