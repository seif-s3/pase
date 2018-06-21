import sys, os
sys.path.insert(1, os.path.join(os.getcwd(), './src'))

import numpy as np
import predictmod.utils as utils


from statsmodels.tsa import arima_model
# from sklearn.metrics import mean_squared_error


class ArimaModel(object):

    def __init__(self):
        self.series = np.genfromtxt(
            '/datasets/instana.csv', delimiter=',', usecols=range(0, 672), invalid_raise=False)

        self.data = utils.load_instana_data()
        # Preprocessing
        self.data_clean = self.data.copy()
        self.data_clean[self.data_clean == -1] = np.nan

        self.data_clean[np.isnan(self.data_clean)] = np.nanmean(self.data_clean)
        self._train_test_split(505, 168)

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
            model = arima_model.ARIMA(history, order=(2, 1, 0))
            model_fit = model.fit(disp=-1)
            output = model_fit.forecast()
            yhat = output[0]
            predictions.append(yhat)
            obs = test[t]
            history.append(yhat)
            if verbose:
                print >> sys.stderr, ('predicted=%f, expected=%f' % (yhat, obs))
        return test, predictions
