from sklearn.model_selection import KFold
from time import perf_counter
from typing import Callable, Tuple

import numpy as np
import pandas as pd
import logging

from pd_utils.train_test_data import make_training_data, make_forecast_data
from pd_utils.utils import log_with_time
from .data_objects import FeaturesAndLabels, Model, ClassificationSummary, Fit


log = logging.getLogger(__name__)


def fit_classifier(df: pd.DataFrame,
                   features_and_labels: FeaturesAndLabels,
                   model_provider: Callable[[int], Model],
                   test_size: float = 0.4,
                   number_of_cross_validation_splits: int = None,
                   cache_feature_matrix: bool = False,
                   test_validate_split_seed = 42,
                   summary_printer: Callable[[np.ndarray, np.ndarray, np.ndarray], None] = None
                   ) -> Tuple[Model, ClassificationSummary, ClassificationSummary]:
    x_train, x_test, y_train, y_test, index_train, index_test, min_required_data, names = \
        make_training_data(df,
                           features_and_labels,
                           test_size,
                           int,
                           test_validate_split_seed,
                           cache=cache_feature_matrix,
                           summary_printer=summary_printer)

    log.info(f"create model (min required data = {min_required_data}")
    model = model_provider(min_required_data=min_required_data)

    start_performance_count = log_with_time(lambda: log.info("fit model"))
    if number_of_cross_validation_splits is not None:
        # cross validation
        cv = KFold(n_splits = number_of_cross_validation_splits)
        folds = cv.split(x_train, y_train)

        for f, (train_idx, test_idx) in enumerate(folds):
            log.info(f'fit fold {f}')
            model.fit(x_train[train_idx], y_train[train_idx], x_train[test_idx], y_train[test_idx])
    else:
        # fit without cross validation
        model.fit(x_train, y_train, x_test, y_test)

    log.info(f"fitting model done in {perf_counter() - start_performance_count: .2f} sec!")

    # assemble the result objects
    pc = features_and_labels.probability_cutoff
    loss = df[features_and_labels.loss_column if features_and_labels.loss_column is not None else []]
    training_classification = ClassificationSummary(y_train, model.predict(x_train), index_train, loss, pc)
    test_classification = ClassificationSummary(y_test, model.predict(x_test), index_test, loss, pc)
    return Fit(model, training_classification, test_classification)


def backtest(df: pd.DataFrame,
             features_and_labels: FeaturesAndLabels,
             model: Model) -> ClassificationSummary:

    # make training and test data with no 0 test data fraction
    x, _, y, _, index, _, _, names = make_training_data(df, features_and_labels, 0, int)

    # precidict probabilities
    y_hat = model.predict(x)

    return ClassificationSummary(y, y_hat, index, df[features_and_labels.loss_column], features_and_labels.probability_cutoff)


def classify(df: pd.DataFrame,
             features_and_labels: FeaturesAndLabels,
             model: Model) -> pd.DataFrame:

    # first save target columns
    target = df[features_and_labels.target_columns] if features_and_labels.target_columns is not None else None

    # then re assign data frame with features only
    dff, x, _ = make_forecast_data(df, features_and_labels)

    # predict on features
    prediction = model.predict(x)
    pc = features_and_labels.probability_cutoff

    # return result
    dff["prediction"] = prediction > pc
    dff["prediction_proba"] = prediction
    dff["target"] = target
    return dff