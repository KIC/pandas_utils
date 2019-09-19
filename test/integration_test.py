import pandas as pd
import numpy as np
import unittest
import pd_utils as pdu

from sklearn.neural_network import MLPClassifier

import logging


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class IntegrationTest(unittest.TestCase):

    def test_fit_classifier(self):
        df = pd.read_csv(f'{__name__}.csv', index_col='Date')
        df['label'] = df["spy_Close"] > df["spy_Open"]

        fit = df.fit_classifier(pdu.FeaturesAndLabels(features=['vix_Close'], labels=['label']),
                                pdu.SkitModel(MLPClassifier(activation='tanh', hidden_layer_sizes=(60, 50), alpha=0.001,
                                                            random_state=42)),
                                test_size=0.4,
                                test_validate_split_seed=42)

        self.assertEqual(fit.model.min_required_data, 1)
        np.testing.assert_array_equal(fit.test_classification.confusion_count(), np.array([[744, 586],
                                                                                           [655, 698]]))