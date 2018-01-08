import unittest

from enjoliver.monitoring import DatabaseMonitoring


class TestMonitoring(unittest.TestCase):
    def test_01(self):
        one = DatabaseMonitoring()
        two = DatabaseMonitoring()
        self.assertIs(one, two)
