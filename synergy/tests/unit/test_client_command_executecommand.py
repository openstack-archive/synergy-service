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
Test the ExecuteCommand class.

"""

import mock

from synergy.client.command import ExecuteCommand
from synergy.client.command import HTTPCommand
from synergy.tests import base


class TestExecuteCommand(base.TestCase):

    def setUp(self):
        super(TestExecuteCommand, self).setUp()
        self.execute_command = ExecuteCommand(name="dummy_execmd")

    def test_execute_no_args(self):
        """Check the URL and payload."""
        with mock.patch.object(HTTPCommand, 'execute') as m:
            self.execute_command.execute(
                synergy_url="",
                manager="Manager",
                command="command")

        expected_payload = {
            "manager": "Manager",
            "command": "command",
            "args": "{}"}
        m.assert_called_once_with("/synergy/execute", expected_payload)

    def test_execute_with_args(self):
        """Check the URL and payload."""
        with mock.patch.object(HTTPCommand, 'execute') as m:
            self.execute_command.execute(
                synergy_url="",
                manager="Manager",
                command="command",
                args={"test": {"what": "yes"}})

        expected_payload = {
            "manager": "Manager",
            "command": "command",
            "args": '{"test": {"what": "yes"}}'}
        m.assert_called_once_with("/synergy/execute", expected_payload)
