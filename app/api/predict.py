from app import api

from flask_restful import rest

class Predict(rest.Resource):

	def get(self):
		test, predictions = train_model_on_batch(training_data, testing_data)
	    return predictions

api.add_resource(Predict, '/v0/predict')