import numpy as np
import pandas as pd
import logging

from time import perf_counter as pc
from typing import Tuple

from pandas_ml_utils.model.features_and_labels.features_and_labels_extractor import FeatureTargetLabelExtractor
from pandas_ml_utils.utils.functions import log_with_time

_log = logging.getLogger(__name__)


def make_backtest_data(df: pd.DataFrame, features_and_labels: FeatureTargetLabelExtractor):
    return make_training_data(df, features_and_labels, 0)


def make_training_data(features_and_labels: FeatureTargetLabelExtractor,
                       test_size: float = 0.4,
                       youngest_size: float = None,
                       seed: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list, list]:
    # only import if this method is needed
    from sklearn.model_selection import train_test_split

    # use only feature and label columns
    start_pc = log_with_time(lambda: _log.debug("make training / test data split ..."))

    # get features and labels
    df_features_and_labels, x, y = features_and_labels.features_labels
    index = df_features_and_labels.index.tolist()

    # split training and test data
    start_split_pc = log_with_time(lambda: _log.debug("  splitting ..."))

    if test_size <= 0:
        x_train, x_test, y_train, y_test, index_train, index_test = (x, None, y, None, index, None)
    elif seed == 'youngest':
        i = int(len(index) - len(index) * test_size)
        x_train, x_test = x[:i], x[i:]
        y_train, y_test = y[:i], y[i:]
        index_train, index_test = index[:i], index[i:]
    else:
        random_sample_test_size = test_size if youngest_size is None else test_size * (1 - youngest_size)
        random_sample_train_index_size = int(len(index) - len(index) * (test_size - random_sample_test_size))

        if random_sample_train_index_size < len(index):
            _log.warning(f"keeping youngest {len(index) - random_sample_train_index_size} elements in test set")

            # cut the youngest data and use residual to randomize train/test data
            x_train, x_test, y_train, y_test, index_train, index_test = \
                train_test_split(x[:random_sample_train_index_size],
                                 y[:random_sample_train_index_size],
                                 index[:random_sample_train_index_size],
                                 test_size=random_sample_test_size, random_state=seed)

            # then concatenate (add back) the youngest data to the random test data
            x_test = np.vstack([x_test, x[random_sample_train_index_size:]])
            y_test = np.vstack([y_test, y[random_sample_train_index_size:]])
            index_test = np.hstack([index_test, index[random_sample_train_index_size:]])  # index is 1D
        else:
            x_train, x_test, y_train, y_test, index_train, index_test = \
                train_test_split(x, y, index, test_size=random_sample_test_size, random_state=seed)

    _log.info(f"  splitting ... done in {pc() - start_split_pc: .2f} sec!")
    _log.info(f"make training / test data split ... done in {pc() - start_pc: .2f} sec!")

    # return the split
    return x_train, x_test, y_train, y_test, index_train, index_test


def make_forecast_data(features_and_labels: FeatureTargetLabelExtractor):
    return features_and_labels.features

