import logging
import unittest

import numpy as np
import pandas as pd
from keras.layers import Dense, Activation, Flatten
from keras.models import Sequential
from keras.optimizers import Adam
from rl.agents import SARSAAgent
from rl.policy import MaxBoltzmannQPolicy
from sklearn.model_selection import KFold
from sklearn.neural_network import MLPClassifier, MLPRegressor

import pandas_ml_utils as pdu
from pandas_ml_utils.analysis.correlation_analysis import _sort_correlation

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class ComponentTest(unittest.TestCase):

    def test_fit_classifier_full(self):
        df = pd.read_csv(f'{__name__}.csv', index_col='Date')
        df['label'] = df["spy_Close"] > df["spy_Open"]

        # fit
        fit = df.fit_classifier(pdu.SkitModel(MLPClassifier(activation='tanh', hidden_layer_sizes=(60, 50), alpha=0.001,
                                                            random_state=42),
                                              pdu.FeaturesAndLabels(features=['vix_Close'], labels=['label'],
                                                                    targets=("vix_Open", "spy_Volume"))),
                                test_size=0.4,
                                test_validate_split_seed=42)

        self.assertEqual(fit.model.features_and_labels.min_required_samples, 1)
        np.testing.assert_array_equal(fit.training_summary.get_confusion_matrix()['vix_Open'], np.array([[1067,  872], [1002, 1082]]))
        np.testing.assert_array_equal(fit.test_summary.get_confusion_matrix()['vix_Open'], np.array([[744, 586], [655, 698]]))

        # backtest
        fitted_model = fit.model
        backtest_classification = df.backtest_classifier(fitted_model)
        np.testing.assert_array_equal(backtest_classification.get_confusion_matrix()['vix_Open'], np.array([[1811, 1458], [1657, 1780]]))

        # classify
        fitted_model = fit.model
        classified_df = df.classify(fitted_model)
        print(classified_df.tail())

        self.assertEqual(len(classified_df[classified_df["vix_Open", "prediction", "value"] == False]), 3437)
        self.assertTrue(classified_df["vix_Open", "prediction", "value_proba"].sum() > 0)
        self.assertTrue(classified_df["vix_Open", "prediction", "value_proba"].min() > 0)
        self.assertTrue(classified_df["vix_Open", "prediction", "value_proba"].max() < 1)
        self.assertListEqual(classified_df.columns.tolist(),
                             [('vix_Open', 'prediction', 'value'), ('vix_Open', 'prediction', 'value_proba'), ('vix_Open', 'target', 'value')])

        # classify tail
        fitted_model = fit.model
        classified_df = df.classify(fitted_model, 2)
        self.assertEqual(len(classified_df), 2)
