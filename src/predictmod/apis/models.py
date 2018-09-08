from predictmod.app import api, mongo
import flask_restful as rest
import flask


class Models(rest.Resource):

    def get(self):
        # Fetch all models in db
        try:
            all_models = mongo.models.find()
        except Exception as e:
            return flask.jsonify(
                {
                    'status': '500',
                    'message': e.message
                }
            )
        return flask.jsonify(all_models)


api.add_resource(Models, '/models')
