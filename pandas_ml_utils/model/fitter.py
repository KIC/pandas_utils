from __future__ import annotations

import logging
from time import perf_counter
from typing import Callable, Tuple, Dict, TYPE_CHECKING
from sklearn.utils.testing import ignore_warnings
from sklearn.exceptions import ConvergenceWarning

import numpy as np
import pandas as pd

from pandas_ml_utils.model.features_and_labels_utils.extractor import FeatureTargetLabelExtractor
from pandas_ml_utils.model.fit import Fit
from ..train_test_data import make_training_data, make_forecast_data
from ..utils.functions import log_with_time
from ..model.models import Model
from ..constants import *

_log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from hyperopt import Trials


def fit(df: pd.DataFrame,
         model_provider: Callable[[int], Model],
         test_size: float = 0.4,
         cross_validation: Tuple[int, Callable[[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]]] = None,
         test_validate_split_seed = 42,
         hyper_parameter_space: Dict = None
         ) -> Fit:
    """

    :param df: the DataFrame you apply this function to
    :param model_provider: a callable which provides a new :class:`.Model` instance i.e. for each hyper parameter if
                           hyper parameter tuning is enforced. Usually all the Model subclasses implement __call__
                           thus they are a provider of itself
    :param test_size: the fraction [0, 1] of samples which are used for a test set
    :param cross_validation: tuple of number of epochs for each fold provider and a cross validation provider
    :param test_validate_split_seed: seed if train, test split needs to be reproduceable
    :param hyper_parameter_space: space of hyper parameters passed as kwargs to your model provider
    :return: returns a :class:`.Fit` object
    """

    trails = None
    model = model_provider()
    features_and_labels = FeatureTargetLabelExtractor(df, model.features_and_labels)

    # make training and test data sets
    x_train, x_test, y_train, y_test, index_train, index_test = \
        make_training_data(features_and_labels,
                           test_size,
                           seed=test_validate_split_seed)

    _log.info(f"create model ({features_and_labels})")

    # eventually perform a hyper parameter optimization first
    start_performance_count = log_with_time(lambda: _log.info("fit model"))
    if hyper_parameter_space is not None:
        # next isolate hyperopt parameters and constants only used for hyper parameter tuning like early stopping
        constants = {}
        hyperopt_params = {}
        for k, v in list(hyper_parameter_space.items()):
            if k.startswith("__"):
                hyperopt_params[k[2:]] = hyper_parameter_space.pop(k)
            elif type(v) in [int, float, bool]:
                constants[k] = hyper_parameter_space.pop(k)

        # optimize hyper parameters
        model, trails = __hyper_opt(hyper_parameter_space,
                                    hyperopt_params,
                                    constants,
                                    model_provider,
                                    cross_validation,
                                    x_train, y_train, index_train,
                                    x_test, y_test, index_test)

    # finally train the model with eventually tuned hyper parameters
    __train_loop(model, cross_validation, x_train, y_train, index_train, x_test, y_test, index_test)
    _log.info(f"fitting model done in {perf_counter() - start_performance_count: .2f} sec!")

    # assemble result objects
    df_train = features_and_labels.prediction_to_frame(model.predict(x_train), index=index_train, inclusive_labels=True)
    df_test = features_and_labels.prediction_to_frame(model.predict(x_test), index=index_test, inclusive_labels=True) if x_test is not None else None

    return Fit(model, model.summary_provider(df_train), model.summary_provider(df_test), trails)


def __train_loop(model, cross_validation, x_train, y_train, index_train,  x_test, y_test, index_test):
    if cross_validation is not None and isinstance(cross_validation, Tuple) and callable(cross_validation[1]):
        losses = []
        for fold_epoch in range(cross_validation[0]):
            # cross validation, make sure we re-shuffle every fold_epoch
            for f, (train_idx, test_idx) in enumerate(cross_validation[1](x_train, y_train)):
                _log.info(f'fit fold {f}')
                loss = model.fit(x_train[train_idx], y_train[train_idx], x_train[test_idx], y_train[test_idx],
                                 index_train[train_idx], index_train[test_idx])

                losses.append(loss)

        return np.array(losses).mean()
    else:
        # fit without cross validation
        return model.fit(x_train, y_train, x_test, y_test, index_train, index_test)


@ignore_warnings(category=ConvergenceWarning)
def __hyper_opt(hyper_parameter_space,
                hyperopt_params,
                constants,
                model_provider,
                cross_validation,
                x_train, y_train, index_train,
                x_test, y_test, index_test):
    from hyperopt import fmin, tpe, Trials

    keys = list(hyper_parameter_space.keys())

    def f(args):
        sampled_parameters = {k: args[i] for i, k in enumerate(keys)}
        model = model_provider(**sampled_parameters, **constants)
        loss = __train_loop(model, cross_validation, x_train, y_train, index_train, x_test, y_test, index_test)
        if loss is None:
            raise ValueError("Can not hyper tune if model loss is None")

        return {'status': 'ok', 'loss': loss, 'parameter': sampled_parameters}

    trails = Trials()
    fmin(f, list(hyper_parameter_space.values()), algo=tpe.suggest, trials=trails, show_progressbar=False, **hyperopt_params)

    # find the best parameters amd make sure to NOT pass the constants as they are only used for hyperopt
    best_parameters = trails.best_trial['result']['parameter']
    best_model = model_provider(**best_parameters)

    print(f'best parameters: {repr(best_parameters)}')
    return best_model, trails


def _backtest(df: pd.DataFrame, model: Model) -> pd.DataFrame:
    features_and_labels = model.features_and_labels

    # make training and test data with no 0 test data fraction
    x, _, y, _, index, _ = make_training_data(df, features_and_labels, 0, int)

    # predict probabilities
    df = features_and_labels.prediction_to_frame(model.predict(x), index=index, inclusive_labels=True)
    # TODO later return Fit object using model.summary_provider so we can et rid of df.backtest_xxx
    return df


# TODO DELETE everything below this comment
def _predict(df: pd.DataFrame, model: Model, tail: int = None) -> pd.DataFrame:
    features_and_labels = model.features_and_labels
    goals = features_and_labels.get_goals()

    if tail is not None:
        if tail <= 0:
            raise ValueError("tail must be > 0 or None")
        elif features_and_labels.min_required_samples is not None:
            # just use the tail for feature engineering
            df = df[-(tail + (features_and_labels.min_required_samples - 1)):]
        else:
            _log.warning("could not determine the minimum required data from the model")

    # predict and return data frame
    dff, x = make_forecast_data(df, features_and_labels)
    df_prediction = __predict(df.loc[dff.index], model, x)

    header = __stack_header_prediction(goals)
    df_prediction.columns = pd.MultiIndex.from_tuples(header)

    return df_prediction


def __predict(df, model, x):
    # first save target columns and loss column
    goals = model.features_and_labels.get_goals()
    predictions = model.predict(x)
    df_pred = pd.DataFrame({}, index=df.index)

    for target, (_, labels) in goals.items():
        prediction = predictions[target]
        postfix = "" if target is None else f'_{target}'

        if target is not None:
            df_pred[f'{TARGET_COLUMN_NAME}_{target}'] = df[target]
        else:
            df_pred[f"{TARGET_COLUMN_NAME}"] = ""

        if len(labels) > 1:
            for i, label in enumerate(labels):
                df_pred[f"{PREDICTION_COLUMN_NAME}{postfix}_{label}"] = prediction[:, i]
        else:
            df_pred[f"{PREDICTION_COLUMN_NAME}{postfix}"] = prediction

    return df_pred


def __loss(df, model):
    df_loss = pd.DataFrame({}, index=df.index)
    goals = model.features_and_labels.get_goals()
    for target, (loss, _) in goals.items():
        postfix = f"_{target}" if len(goals) > 1 else ""
        if loss in df.columns:
            df_loss[f"{LOSS_COLUMN_NAME}{postfix}_{loss}"] = df[loss]
        else:
            df_loss[f"{LOSS_COLUMN_NAME}{postfix}"] = -abs(loss) if loss is not None else -1.0

    return df_loss


def __truth(df, model):
    df_truth = pd.DataFrame({}, index=df.index)
    goals = model.features_and_labels.get_goals()

    for target, (_, labels) in goals.items():
        postfix = "" if target is None else f'_{target}'
        for label in labels:
            postfix2 = "" if len(labels) <= 1 else f"_{label}"
            df_truth[f"{LABEL_COLUMN_NAME}{postfix}{postfix2}"] = df[label]

    return df_truth


def __stack_header_prediction(goals):
    prediction_headers = []
    # prediction
    for target, (loss, labels) in goals.items():
        prediction_headers.append((target or TARGET_COLUMN_NAME, TARGET_COLUMN_NAME, "value"))
        for l in labels:
            prediction_headers.append((target or TARGET_COLUMN_NAME, PREDICTION_COLUMN_NAME, l if len(labels) > 1 else "value"))

    return prediction_headers


def __stack_header_label(goals):
    return [(target or TARGET_COLUMN_NAME, LABEL_COLUMN_NAME, l if len(labels) > 1 else "value") for target, (_, labels) in goals.items() for l in labels ]


def __stack_header_loss(goals):
    return [(target or TARGET_COLUMN_NAME, LOSS_COLUMN_NAME, "value") for target, (loss, _) in goals.items()]
