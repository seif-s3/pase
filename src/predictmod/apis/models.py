from predictmod.app import api, mongo
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
                    'message': 'Error Decoding Result'
                }
            )

        return flask.jsonify(docs)


api.add_resource(Models, '/models')
