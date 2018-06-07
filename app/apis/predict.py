from app import api
from forecast_models.arima import ArimaModel
import flask_restful as rest


class Predict(rest.Resource):

    def get(self):
        model = ArimaModel()
        test, predictions = model.train_model_on_batch(model.training_data, model.testing_data)
        return predictions

api.add_resource(Predict, '/v0/predict')
