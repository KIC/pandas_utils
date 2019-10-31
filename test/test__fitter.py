import pandas as pd
from unittest import TestCase

from pandas_ml_utils.model.models import *
from pandas_ml_utils.model.fitter import _fit, _backtest, _predict

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.svm import LinearSVC


df = pd.DataFrame({"a": np.array([0.1, 0.01]), "b": np.array([True, False]), "c": np.array([False, True])})

class TestFitter(TestCase):

    def test__fit(self):
        """given"""
        features_and_labels = FeaturesAndLabels(["a"], ["b"])
        providers = [
            SkitModel(MLPClassifier(activation='tanh', hidden_layer_sizes=(1, 1), alpha=0.001, random_state=42),
                      features_and_labels, foo='bar'),
            SkitModel(LogisticRegression(), features_and_labels),
            SkitModel(LinearSVC(), features_and_labels),
            SkitModel(RandomForestClassifier(), features_and_labels)]

        """when"""
        fitts = [_fit(df, p, 0)[1][0] for p in providers]
        fits_df_columns = [f.columns.tolist() for f in fitts]

        """then"""
        expected_columns = [('target', 'target', 'value'), ('target', 'prediction', 'value'), ('target', 'label', 'value'), ('target', 'loss', 'value')]
        self.assertListEqual(fits_df_columns[0], expected_columns)
        self.assertListEqual(fits_df_columns[1], expected_columns)
        self.assertListEqual(fits_df_columns[2], expected_columns)
        self.assertListEqual(fits_df_columns[3], expected_columns)
        np.testing.assert_array_equal(fitts[0]["target", "label", "value"].values, df["b"].values)
        np.testing.assert_array_equal(fitts[1]["target", "label", "value"].values, df["b"].values)
        np.testing.assert_array_equal(fitts[2]["target", "label", "value"].values, df["b"].values)
        np.testing.assert_array_equal(fitts[3]["target", "label", "value"].values, df["b"].values)

    def test__backtest(self):
        """given"""
        fls = [FeaturesAndLabels(["a"], ["b"]),
               FeaturesAndLabels(["a"], ["b"], targets="b"),
               FeaturesAndLabels(["a"], ["b", "c"], targets={"b": (-1, ["b", "c"])}),
               FeaturesAndLabels(["a"], ["b", "c"], targets={"b": (-1, ["b", "c"]), "a": (-2, ["b", "c"])})]

        providers = [SkitModel(MLPRegressor(activation='tanh', hidden_layer_sizes=(1, 1), alpha=0.001, random_state=42),
                               features_and_labels=fl) for fl in fls]

        """when"""
        fitted_models = [_fit(df, p, 0)[0] for p in providers]
        backtests = [_backtest(df, fm) for fm in fitted_models]
        backtest_columns = [b.columns.tolist() for b in backtests]

        """then"""
        # print(backtest_columns[3])
        self.assertEqual(backtest_columns[0], [('target', 'target', 'value'), ('target', 'prediction', 'value'), ('target', 'label', 'value'), ('target', 'loss', 'value'), ('feature', 'feature', 'a')])
        self.assertEqual(backtest_columns[1], [('b', 'target', 'value'), ('b', 'prediction', 'value'), ('b', 'label', 'value'), ('b', 'loss', 'value'), ('feature', 'feature', 'a')])
        self.assertEqual(backtest_columns[2], [('b', 'target', 'value'), ('b', 'prediction', 'b'), ('b', 'prediction', 'c'), ('b', 'label', 'b'), ('b', 'label', 'c'), ('b', 'loss', 'value'), ('feature', 'feature', 'a')])
        self.assertEqual(backtest_columns[3], [('b', 'target', 'value'), ('b', 'prediction', 'b'), ('b', 'prediction', 'c'), ('a', 'target', 'value'), ('a', 'prediction', 'b'), ('a', 'prediction', 'c'), ('b', 'label', 'b'), ('b', 'label', 'c'), ('a', 'label', 'b'), ('a', 'label', 'c'), ('b', 'loss', 'value'), ('a', 'loss', 'value'), ('feature', 'feature', 'a')])
        np.testing.assert_array_equal(backtests[3]["b", "label", "b"].values, df["b"].values)
        np.testing.assert_array_equal(backtests[3]["a", "label", "b"].values, df["b"].values)
        np.testing.assert_array_equal(backtests[3]["b", "label", "c"].values, df["c"].values)
        np.testing.assert_array_equal(backtests[3]["a", "label", "c"].values, df["c"].values)
        np.testing.assert_array_equal(backtests[3]["a", "loss", "value"].values, -2)
        np.testing.assert_array_equal(backtests[3]["b", "loss", "value"].values, -1)

    def test__predict(self):
        """given"""
        fls = [FeaturesAndLabels(["a"], ["b"]),
               FeaturesAndLabels(["a"], ["b"], targets="b"),
               FeaturesAndLabels(["a"], ["c", "b"], targets={"b": (-1, ["b", "c"])}),
               FeaturesAndLabels(["a"], ["c", "b"], targets={"b": (-1, ["b", "c"]), "a": (-1, ["b", "c"])})]

        providers = [SkitModel(MLPRegressor(activation='tanh', hidden_layer_sizes=(1, 1), alpha=0.001, random_state=42),
                               features_and_labels=fl) for fl in fls]


        """when"""
        fitted_models = [_fit(df, p, 0)[0] for p in providers]

        """then"""
        predictions = [_predict(df, fm) for fm in fitted_models]
        print(predictions[-1].columns.tolist())
        self.assertEqual(predictions[0].columns.tolist(), [('feature', 'feature', 'a'), ('target', 'target', 'value'), ('target', 'prediction', 'value')])
        self.assertEqual(predictions[1].columns.tolist(), [('feature', 'feature', 'a'), ('b', 'target', 'value'), ('b', 'prediction', 'value')])
        self.assertEqual(predictions[2].columns.tolist(), [('feature', 'feature', 'a'), ('b', 'target', 'value'), ('b', 'prediction', 'b'), ('b', 'prediction', 'c')])
        self.assertEqual(predictions[3].columns.tolist(), [('feature', 'feature', 'a'), ('b', 'target', 'value'), ('b', 'prediction', 'b'), ('b', 'prediction', 'c') , ('a', 'target', 'value'), ('a', 'prediction', 'b'), ('a', 'prediction', 'c')])


