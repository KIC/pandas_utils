from unittest import TestCase

from pandas_ml_utils.model.features_and_Labels import FeaturesAndLabels


class TestFeaturesAndLabels(TestCase):

    def test_id(self):
        """given"""
        fl1 = FeaturesAndLabels(["a", "b", "c"], ["d", "e"], targets={"b": None})
        fl2 = FeaturesAndLabels(["a", "b", "c"], ["d", "e"], targets={"b": None})
        fl3 = FeaturesAndLabels(["a", "b", "d"], ["d", "e"], targets={"b": None})

        """expect"""
        self.assertEqual(fl1.__id__(), fl2.__id__())
        self.assertEqual(hash(fl2), hash(fl2))
        self.assertNotEqual(hash(fl2), hash(fl3))

    def test_1d(self):
        """given"""
        fl = FeaturesAndLabels(["a", "b", "c"], ["d", "e"])

        """when"""
        shape = fl.shape()

        """then"""
        self.assertEqual(shape, ((3, ), (2, )))


    def test_2d(self):
        """given"""
        fl = FeaturesAndLabels(["a", "b", "c"], ["d", "e"], feature_lags=range(4))

        """when"""
        shape = fl.shape()

        """then"""
        # shape is ((timesteps, features), (labels, )
        self.assertEqual(shape, ((4, 3), (2, )))

    def test_goals(self):
        """given"""
        fl1 = FeaturesAndLabels(["a", "b", "c"], ["d", "e"], targets='a')
        fl2 = FeaturesAndLabels(["a", "b", "c"], ["d", "e"], targets=('a', 'b'))
        fl3 = FeaturesAndLabels(["a", "b", "c"], ["d", "e"], targets={'a': 'b'})
        fl4 = FeaturesAndLabels(["a", "b", "c"], ["d", "e"], targets={'a': ('b', 'd')})
        fl5 = FeaturesAndLabels(["a", "b", "c"], ["d", "e"], targets={'a': ('b', ['d'])})

        """when"""
        g1 = fl1.get_goals()
        g2 = fl2.get_goals()
        g3 = fl3.get_goals()
        g4 = fl4.get_goals()
        g5 = fl5.get_goals()

        """then"""
        self.assertEqual(g1, {'a': (None, ["d", "e"])})
        self.assertEqual(g2, {'a': ('b', ["d", "e"])})
        self.assertEqual(g3, {'a': ('b', ["d", "e"])})
        self.assertEqual(g4, {'a': ('b', ["d"])})
        self.assertEqual(g5, {'a': ('b', ["d"])})