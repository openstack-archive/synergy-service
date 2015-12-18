# coding: utf-8

import unittest

from synergy.common.manager import Manager


class TestManager(unittest.TestCase):

    def setUp(self):
        self.manager = Manager(name="dummy_manager")

    def test_name(self):
        self.assertEqual(self.manager.getName(), "dummy_manager")
