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
Tests a simple implementation of the Manager class.

"""

from synergy.common.manager import Manager
from synergy.tests import base


class SimpleManager(Manager):
    """Simple implementation of the Manager class.

    This class maintains an integer counter.
    The manager task is to increment the counter by one.
    Only one event is possible: increment the counter by 10.
    The counter is set to 0 on setup, not on init.
    """

    def __init__(self, name):
        super(SimpleManager, self).__init__(name)
        self._counter = None

    def _reset_counter(self):
        self._counter = None

    def execute(self, command, *args, **kargs):
        if command == "RESET":
            self._reset_counter()

    def task(self):
        self._counter += 1

    def doOnEvent(self, event_type, *args, **kargs):
        if event_type == "JUMP10":
            self._counter += 10

    def setup(self):
        self._counter = 0

    def destroy(self):
        self._counter = None


class TestManagerImplementation(base.TestCase):

    def setUp(self):
        super(TestManagerImplementation, self).setUp()
        self.manager = SimpleManager(name="simple_manager")
        # We set the manager list to be the manager itself for the sake of
        # simplicity.
        self.manager.managers = {"simple_manager": self.manager}

    def test_execute(self):
        self.manager.setup()
        self.manager.execute("RESET")
        self.assertIsNone(self.manager._counter)

    def test_notify(self):
        self.manager.setup()
        self.manager.notify(event_type="JUMP10", manager_name="simple_manager")
        self.assertEqual(10, self.manager._counter)

    def test_setup(self):
        self.assertIsNone(self.manager._counter)
        self.manager.setup()
        self.assertEqual(0, self.manager._counter)

    def test_destroy(self):
        self.manager.setup()
        self.manager.destroy()
        self.assertIsNone(self.manager._counter)

    def test_do_on_event(self):
        self.manager.setup()
        self.manager.doOnEvent(event_type="JUMP10")
        self.assertEqual(10, self.manager._counter)

    def test_run_stop(self):
        self.manager.setup()
        self.manager.rate = 1.0 / 60 / 1000  # to sleep only 1 ms and not 1 min

        self.manager.start()
        self.assertEqual(True, self.manager.isAlive())

        self.manager.stop()
        self.assertEqual(False, self.manager.isAlive())
