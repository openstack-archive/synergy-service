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


try:
    import unittest2 as unittest
except ImportError:
    import unittest

import json
import logging
import mock
import sys
import time

from mock import Mock
from synergy.service import Synergy

logging.basicConfig(level=logging.DEBUG)

LOG = logging.getLogger("SynergyTests")
LOG.setLevel(logging.DEBUG)


def getLogger(name):
    formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                  "%(levelname)s - %(message)s")

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.addHandler(ch)

    return logger


class SynergyTests(unittest.TestCase):

    @mock.patch('synergy.service.LOG', LOG)
    def setUp(self):
        super(SynergyTests, self).setUp()

        self.synergy = Synergy()
        self.synergy.managers["TimerManager"].start()
        time.sleep(1)

    @mock.patch('synergy.service.LOG', LOG)
    def test_managers(self):
        self.assertEqual(self.synergy.managers.keys(), ["TimerManager"])

    @mock.patch('synergy.service.LOG', LOG)
    def test_listManagers(self):
        start_response = Mock()
        result = self.synergy.listManagers(environ={},
                                           start_response=start_response)
        result = json.loads(result[0])

        self.assertEqual(result, ["TimerManager"])

    @mock.patch('synergy.service.LOG', LOG)
    def test_getManagerStatus(self):
        start_response = Mock()
        result = self.synergy.getManagerStatus(environ={},
                                               start_response=start_response)
        result = json.loads(result[0])

        self.assertEqual(result, {'TimerManager': 'ACTIVE'})

    @mock.patch('synergy.service.LOG', LOG)
    def test_startManager(self):
        environ = {'QUERY_STRING': 'manager=TimerManager'}
        start_response = Mock()

        result = self.synergy.startManager(environ, start_response)
        result = json.loads(result[0])

        self.assertEqual(result, {'TimerManager': {
            'message': 'started successfully', 'status': 'RUNNING'}})

        time.sleep(0.5)

        result = self.synergy.startManager(environ, start_response)
        result = json.loads(result[0])

        self.assertEqual(result, {'TimerManager': {
            'message': 'WARN: already started', 'status': 'RUNNING'}})

    @mock.patch('synergy.service.LOG', LOG)
    def test_stopManager(self):
        environ = {'QUERY_STRING': 'manager=TimerManager'}
        start_response = Mock()

        result = self.synergy.startManager(environ, start_response)

        time.sleep(0.5)

        result = self.synergy.stopManager(environ, start_response)

        result = json.loads(result[0])

        self.assertEqual(result, {'TimerManager': {
            'message': 'stopped successfully', 'status': 'ACTIVE'}})

    @mock.patch('synergy.service.LOG', LOG)
    def test_executeCommand(self):
        environ = {'QUERY_STRING': 'manager=TimerManager&command=GET_TIME'}
        start_response = Mock()

        result = self.synergy.executeCommand(environ, start_response)
        result = json.loads(result[0])

        self.assertEqual(result.keys(), ["localtime"])


if __name__ == '__main__':
    unittest.main()
