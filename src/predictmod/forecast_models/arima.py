import sys
import numpy as np
import predictmod.utils as utils
from statsmodels.tsa import arima_model
from predictmod.app import mongo
# from sklearn.metrics import mean_squared_error


# Monkey Patch bug in saving ARIMA class
def __getnewargs__(self):
    return ((self.endog), (self.k_lags, self.k_diff, self.k_ma))
arima_model.ARIMA.__getnewargs__ = __getnewargs__


class ArimaModel(object):

    def _instata(self):
        self.data = utils.load_instana_data()

        # Preprocessing
        self.data_clean = self.data.copy()
        self.data_clean[self.data_clean == -1] = np.nan
        # Replace NaNs with Mean
        self.data_clean[np.isnan(self.data_clean)] = np.nanmean(self.data_clean)

    def __init__(self, load_id=None, dataset=None):
        # TODO: If we are instantiating a new model, train it from the CSV
        # TODO: Parametarize csv file
        if load_id is None and dataset:
            # Instana data has a special format so it will be parsed differently
            if dataset == 'instana-with-timestamps.csv':
                self._instata()
                self._train_test_split(505, 168)
            else:
                # TODO: Add logic for general CSVs here
                self.data_clean = utils.load_dataset(dataset)
                self._train_test_split(
                    int(len(self.data_clean) * 0.7), int(len(self.data_clean) * 0.3))
        else:
            self.load_model(load_id)

    def _train_test_split(self, train, test):
        self.training_data = self.data_clean.head(train)
        self.testing_data = self.data_clean.tail(test)
        print >> sys.stderr, "Training Shape: ", self.training_data.shape
        print >> sys.stderr, "Testing Shape: ", self.testing_data.shape

    def train_model_on_batch(self, training_data, testing_data, verbose=False):
        history = [x[0] for x in training_data.values]
        test = testing_data.values.copy()
        predictions = list()
        for t in range(len(test)):
            self.model = arima_model.ARIMA(history, order=(2, 1, 0))
            self.model_fit = self.model.fit(disp=-1)
            output = self.model_fit.forecast()
            yhat = output[0]
            predictions.append(yhat)
            obs = test[t]
            history.append(yhat)
            if verbose:
                print >> sys.stderr, ('predicted=%f, expected=%f' % (yhat, obs))
        return test, predictions

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
        forecast, stderr, conf_int = self.model_fit.forecast(K)
        return forecast

    def save_model(self, dataset):
        # Make sure we have a saved model
        if self.model_fit:
            # Write model to MongoDB
            mongo_doc = {
                'algorithm': 'ARIMA',
                'input_type': 'csv',    # Whether this model was trained from a batch CSV or Influx
                'input_start': self.data_clean.index.min(),   # Starting timestamp of training data
                'input_end': self.data_clean.index.max(),   # Ending timestamp of training data
                'acquisition_time': utils.utcnow(),
                'metadata': {
                    'p': 2,
                    'd': 1,
                    'q': 0,
                    'dataset': dataset
                }
            }
            inserted = mongo.db.models.insert_one(mongo_doc)
            model_id = inserted.inserted_id
            self.model_fit.save('/trained_models/{}.pkl'.format(model_id))
            return model_id

    def load_model(self, model_id):
        print >> sys.stderr, "Loading model file /trained_models/{}.pkl".format(model_id)
        self.model_fit = arima_model.ARIMAResults.load('/trained_models/{}.pkl'.format(model_id))
