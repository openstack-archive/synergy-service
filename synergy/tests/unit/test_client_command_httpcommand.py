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
Test the HTTPCommand class.

"""

import mock
import requests

from synergy.client.command import HTTPCommand
from synergy.tests import base


class TestHTTPCommand(base.TestCase):

    def setUp(self):
        super(TestHTTPCommand, self).setUp()
        self.http_command = HTTPCommand(name="dummy_httpcmd")

    def test_get_name(self):
        self.assertEqual("dummy_httpcmd", self.http_command.getName())

    def test_configure_parser(self):
        """This method should be implemented in sub-classes."""
        self.assertRaises(
            NotImplementedError,
            self.http_command.configureParser,
            "dummy_subparser")

    def test_execute_success(self):
        mock_response = mock.Mock()
        mock_response.text = '{"test": true}'  # mock a simple json response

        with mock.patch.object(requests, "get", return_value=mock_response)\
                as m:
            result = self.http_command.execute("dummy_url")

        m.assert_called_once_with("dummy_url", headers=None, params=None)
        self.assertEqual({"test": True}, result)
