import os
from unittest import TestCase


class EnvironTestCase(TestCase):
    def test_enjoliver_config(self):
        self.assertIn('ENJOLIVER_CONFIG', os.environ)
