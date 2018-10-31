import sys
import numpy as np
import predictmod.utils as utils
from pyramid.arima import auto_arima
from predictmod.app import mongo
from predictmod import db_helper
import pickle
# from sklearn.metrics import mean_squared_error


class AutoArimaModel(object):

    def _instata(self):
        self.data = utils.load_instana_data()

        # Preprocessing
        self.data_clean = self.data.copy()
        self.data_clean[self.data_clean == -1] = np.nan
        # Replace NaNs with Mean
        self.data_clean[np.isnan(self.data_clean)] = np.nanmean(self.data_clean)

    def __init__(self, retrain=False, load=False, model_id=None, dataset=None, train=0.7, test=0.3):
        if load and retrain is False:
            self.load_model(model_id)
        elif retrain:
            self.retrain_model(model_id)
        elif load is False and retrain is False and dataset:
            # Instana data has a special format so it will be parsed differently
            if dataset == 'instana-with-timestamps.csv':
                self._instata()
                self._train_test_split(505, 168)
            else:
                # Load csv from datasets directory.
                print "Creating AutoARIMA Model from", dataset
                self.data_clean = utils.load_dataset('/datasets/' + dataset)
                self._train_test_split(
                    int(len(self.data_clean) * train), int(len(self.data_clean) * test))

    def _train_test_split(self, train, test):
        self.training_data = self.data_clean.head(train)
        self.testing_data = self.data_clean.tail(test)
        print "Training Shape: ", self.training_data.shape
        print "Testing Shape: ", self.testing_data.shape

    def train_model(self, training_data, testing_data, verbose=False):
        # This tranining will be done in a background thread.
        stepwise_model = auto_arima(training_data, start_p=1, start_q=1,
                                    max_p=5, max_q=5, m=12,
                                    start_P=0, seasonal=True,
                                    d=1, D=1, trace=True,
                                    error_action='ignore',
                                    suppress_warnings=True,
                                    stepwise=True
                                    )

        self.model_fit = stepwise_model.fit(training_data)

    def forecast(self, K):
        # Forecasts K readings in the future
        # Returns
        # -------
        # forecast : array
        #     Array of out of sample forecasts
        # stderr : array
        #     Array of the standard error of the forecasts.
        # conf_int : array
        #     2d array of the confidence interval for the forecast
        forecast = self.model_fit.predict(K)
        return forecast

    # def retrain_model(self, model_id, new_data):
    #     # Adds new observations to model and retrains it for future predictions
    #     print >> sys.stderr, "Retraining AutoARIMA Model ", model_id
    #     if self.model_fit:
    #         self.model_fit.add_new_observations(new_data)

    def pklize(self, model_id):
        print >> sys.stderr, "Saving model file /trained_models/{}.pkl".format(
            model_id)
        with open('/trained_models/{}.pkl'.format(model_id), 'wb') as pklfile:
            pickle.dump(self.model_fit, pklfile)

    def save_model(self, dataset):
        # Make sure we have a saved model
        if self.model_fit:
            # Write model to MongoDB
            mongo_doc = {
                'algorithm': 'AutoARIMA',
                'input_source': 'csv',    # Whether this model is trained from a batch CSV or Influx
                # Starting timestamp of training data
                'input_start': self.data_clean.index.min(),
                'input_end': self.data_clean.index.max(),   # Ending timestamp of training data
                'acquisition_time': utils.utcnow(),
                'metadata': {
                    'start_p': 1,
                    'start_q': 1,
                    'max_p': 5,
                    'max_q': 5,
                    'm': 12,
                    'start_P': 0,
                    'seasonal': True,
                    'd': 1,
                    'D': 1,
                    'trace': True,
                    'error_action': 'ignore',
                    'suppress_warnings': True,
                    'stepwise': True,
                    'dataset': dataset
                }
            }
            inserted = mongo.db.models.insert_one(mongo_doc)
            model_id = inserted.inserted_id
            self.pklize(model_id)
            return model_id

    def load_model(self, model_id):
        print >> sys.stderr, "Loading model file /trained_models/{}.pkl".format(model_id)
        self.model_fit = pickle.load(open('/trained_models/{}.pkl'.format(model_id), 'rb'))
