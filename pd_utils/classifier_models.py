import logging

import dill as pickle
import numpy as np

from pd_utils.train_test_data import reshape_rnn_as_ar

log = logging.getLogger(__name__)


class Model(object):

    @staticmethod
    def load(filename: str):
        with open(filename, 'rb') as file:
            model = pickle.load(file)
            if isinstance(model, Model):
                return model
            else:
                raise ValueError("Deserialized pickle was not a Model!")

    def __init__(self):
        self.min_required_data: int = None

    def save(self, filename: str):
        with open(filename, 'wb') as file:
            pickle.dump(self, file)

    def fit(self, x, y, x_val, y_val) -> None:
        pass

    def predict(self, x) -> np.ndarray:
        pass

    # this lets the model also act as a provider
    def __call__(self, *args, **kwargs):
        log.debug(f'initialize new Model with args: {args}; kwargs: {kwargs}')
        if 'min_required_data' in kwargs:
            self.min_required_data = kwargs['min_required_data']

        return self


class SkitModel(Model):

    def __init__(self, skit_model):
        self.skit_model = skit_model
        self.min_needed_data = None

    def fit(self, x, y, x_val, y_val):
        self.skit_model.fit(reshape_rnn_as_ar(x), y),

    def predict(self, x):
        return self.skit_model.predict_proba(reshape_rnn_as_ar(x))[:, 1]

    def set_min_needed_data(self, min_needed_rows: int):
        self.min_needed_data = min_needed_rows

    def get_min_needed_data(self):
        return self.min_needed_data