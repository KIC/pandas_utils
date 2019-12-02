from unittest import TestCase

import numpy as np
import pandas as pd
from keras import Sequential
from keras.layers import Dense
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.svm import LinearSVC

import pandas_ml_utils as pmu

df = pd.DataFrame({"a": [0.5592344, 0.60739384, 0.19994533, 0.56642537, 0.50965677,
                         0.168989, 0.94080671, 0.76651769, 0.8403563, 0.4003567,
                         0.24295908, 0.50706317, 0.66612371, 0.4020924, 0.21776017,
                         0.32559497, 0.12721287, 0.13904584, 0.65887554, 0.08830925],
                   "b": np.random.randint(2, size=20)})

class TestSaveLoad(TestCase):

    def test_save_load_models(self):
        """given"""
        features_and_labels = pmu.FeaturesAndLabels(["a"], ["b"])


        def keras_model_provider(optimizer='adam'):
            model = Sequential()
            model.add(Dense(1, input_dim=1, activation='sigmoid'))
            model.compile(optimizer, loss='mse')
            return model

        providers = [
            pmu.SkitModel(MLPClassifier(activation='tanh', hidden_layer_sizes=(1, 1), alpha=0.001, random_state=42),
                          features_and_labels, foo='bar'),
            pmu.SkitModel(LogisticRegression(), features_and_labels),
            pmu.SkitModel(LinearSVC(), features_and_labels),
            pmu.SkitModel(RandomForestClassifier(), features_and_labels),
            pmu.KerasModel(keras_model_provider, features_and_labels),
            pmu.MultiModel(pmu.SkitModel(LogisticRegression(), features_and_labels))
        ]

        """when"""
        fits = [df.fit_classifier(mp) for mp in providers]
        models = []
        for i, f in enumerate(fits):
            f.save_model(f'/tmp/pandas-ml-utils-unittest-test_model_{i}')
            models.append((f.model, pmu.Model.load(f'/tmp/pandas-ml-utils-unittest-test_model_{i}')))

        """then"""
        for i, (fitted_model, restored_model) in enumerate(models):
            pd.testing.assert_frame_equal(df.classify(fitted_model), df.classify(restored_model))
            pd.testing.assert_frame_equal(df.backtest_classifier(fitted_model).df, df.backtest_classifier(restored_model).df)