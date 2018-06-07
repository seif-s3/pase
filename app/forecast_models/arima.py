import numpy as np
import utils


from statsmodels.tsa import arima_model
# from sklearn.metrics import mean_squared_error


class ArimaModel(object):

    def __init__(self):
        self.series = np.genfromtxt(
            '../datasets/instana.csv', delimiter=',', usecols=range(0, 672), invalid_raise=False)

        self.data = utils.load_instana_data()

        self.data_clean = self.data.copy()
        self.data_clean[self.data_clean == -1] = np.nan

        self.data_clean[np.isnan(self.data_clean)] = np.nanmean(self.data_clean)

    def _train_test_split(self, train_start, train_end, test_start, test_end):
        self.training_data = self.data_clean[train_start:train_end]
        self.testing_data = self.data_clean[test_start:test_end]
        print "Training Shape: ", self.training_data.shape
        print "Testing Shape: ", self.testing_data.shape

    def train_model_on_batch(self, training_data, testing_data, verbose=False):
        history = [x[0] for x in training_data.values]
        test = testing_data.values.copy()
        predictions = list()
        for t in range(len(test)):
            self.model = arima_model.ARIMA(history, order=(2, 1, 0))
            model_fit = self.model.fit(disp=-1)
            output = model_fit.forecast()
            yhat = output[0]
            predictions.append(yhat)
            obs = test[t]
            history.append(obs)
            if verbose:
                print('predicted=%f, expected=%f' % (yhat, obs))
        return test, predictions
