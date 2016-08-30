# coding: utf-8
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""
Tests the (almost) abstract Manager class.

Since most of the functionalities of this class are present only in an
implementation of the class, we can just do very basic testing.
"""

from synergy.common.manager import Manager
from synergy.tests import base


class TestManager(base.TestCase):

    def setUp(self):
        super(TestManager, self).setUp()
        self.manager = Manager(name="dummy_manager")
        self.manager.setAutoStart(False)

    def test_get_name(self):
        self.assertEqual("dummy_manager", self.manager.getName())

    def test_get_managers_empty(self):
        self.assertEqual({}, self.manager.getManagers())

    def test_get_options(self):
        self.assertEqual([], self.manager.getOptions())

    def test_is_autostart(self):
        self.assertEqual(False, self.manager.isAutoStart())

    def test_set_autostart(self):
        self.manager.setAutoStart(True)
        self.assertEqual(True, self.manager.isAutoStart())

    def test_get_rate(self):
        self.assertEqual(-1, self.manager.getRate())

    def test_set_rate(self):
        self.manager.setRate(10)
        self.assertEqual(10, self.manager.getRate())

    def test_get_status(self):
        self.assertEqual("CREATED", self.manager.getStatus())

    def test_set_status(self):
        self.manager.setStatus("TEST")
        self.assertEqual("TEST", self.manager.getStatus())
