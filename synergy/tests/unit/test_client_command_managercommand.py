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
Test the ManagerCommand class.

"""

import mock

from argparse import ArgumentParser
from argparse import Namespace
from synergy.client.command import HTTPCommand
from synergy.client.command import ManagerCommand
from synergy.tests import base


class TestManagerCommand(base.TestCase):

    def setUp(self):
        super(TestManagerCommand, self).setUp()
        self.manager_command = ManagerCommand()

    def test_config_parser(self):
        """Check that the manager parser is set well."""
        root_parser = ArgumentParser()
        subs = root_parser.add_subparsers(dest="command_name")
        self.manager_command.configureParser(subs)

        # manager list
        res = root_parser.parse_args(["manager", "list"])
        ns = Namespace(command_name="manager", command="list")
        self.assertEqual(ns, res)

        self.assertRaises(
            SystemExit,
            root_parser.parse_args,
            ["manager", "list", "wrong-argument"])

        # manager status
        res = root_parser.parse_args(["manager", "status"])
        ns = Namespace(command_name="manager", command="status", manager=None)
        self.assertEqual(ns, res)

        res = root_parser.parse_args(["manager", "status", "TestManager"])
        ns = Namespace(
            command_name="manager",
            command="status",
            manager="TestManager")
        self.assertEqual(ns, res)

        res = root_parser.parse_args(
            ["manager", "status", "Test1"])
        ns = Namespace(
            command_name="manager",
            command="status",
            manager="Test1")
        self.assertEqual(ns, res)

        # manager start
        self.assertRaises(
            SystemExit,
            root_parser.parse_args,
            ["manager", "start"])

        res = root_parser.parse_args(["manager", "start", "TestManager"])
        ns = Namespace(
            command_name="manager",
            command="start",
            manager="TestManager")
        self.assertEqual(ns, res)

        res = root_parser.parse_args(
            ["manager", "start", "Test1"])
        ns = Namespace(
            command_name="manager",
            command="start",
            manager="Test1")
        self.assertEqual(ns, res)

        # manager stop
        self.assertRaises(
            SystemExit,
            root_parser.parse_args,
            ["manager", "stop"])

        res = root_parser.parse_args(["manager", "stop", "TestManager"])
        ns = Namespace(
            command_name="manager",
            command="stop",
            manager="TestManager")
        self.assertEqual(ns, res)

        res = root_parser.parse_args(
            ["manager", "stop", "Test1"])
        ns = Namespace(
            command_name="manager",
            command="stop",
            manager="Test1")
        self.assertEqual(ns, res)

    @mock.patch('synergy.client.command.tabulate')
    def test_execute_list(self, mock_tabulate):
        """Check the CLI output of "manager list"."""
        mock_parser = mock.Mock()
        mock_parser.args.command = "list"

        manager_a = mock.Mock()
        manager_a.getName.return_value = "ManagerA"
        manager_b = mock.Mock()
        manager_b.getName.return_value = "ManagerB"
        mgrs = [manager_a, manager_b]

        with mock.patch.object(HTTPCommand, 'execute', return_value=mgrs) as m:
            self.manager_command.execute(synergy_url="", args=mock_parser.args)

        m.assert_called_once_with("/synergy/list")

        headers = ["manager"]
        table = [["ManagerA"], ["ManagerB"]]
        mock_tabulate.assert_called_once_with(
            table,
            headers,
            tablefmt="fancy_grid")

    @mock.patch('synergy.client.command.tabulate')
    def test_execute_status_no_manager(self, mock_tabulate):
        """Check the CLI output of "manager status"."""
        # Mock the parser call
        mock_parser = mock.Mock()
        mock_parser.args.command = "status"
        mock_parser.args.manager = []

        # Mock 2 managers and their statuses
        manager_a = mock.Mock()
        manager_a.getName.return_value = "ManagerA"
        manager_a.getStatus.return_value = "UP"
        manager_a.getRate.return_value = 5
        manager_b = mock.Mock()
        manager_b.getName.return_value = "ManagerB"
        manager_b.getStatus.return_value = "DOWN"
        manager_b.getRate.return_value = 10
        mgrs = [manager_a, manager_b]

        # Execute "manager status"
        with mock.patch.object(HTTPCommand, 'execute', return_value=mgrs) as m:
            self.manager_command.execute(synergy_url="", args=mock_parser.args)

        # Check the executed call when we did "manager status"
        m.assert_called_once_with(
            "/synergy/status",
            {"manager": []})

        # Check the data when we call tabulate
        headers = ["manager", "status", "rate (min)"]
        table = [
            ["ManagerA", "UP", 5],
            ["ManagerB", "DOWN", 10]]
        mock_tabulate.assert_called_once_with(
            table,
            headers,
            tablefmt="fancy_grid")

    @mock.patch('synergy.client.command.tabulate')
    def test_execute_status_one_manager(self, mock_tabulate):
        """Check the CLI output of "manager status ManagerB"."""
        # Mock the parser call
        mock_parser = mock.Mock()
        mock_parser.args.command = "status"
        mock_parser.args.manager = ["ManagerB"]

        # Mock a manager and its status
        manager_b = mock.Mock()
        manager_b.getName.return_value = "ManagerB"
        manager_b.getStatus.return_value = "DOWN"
        manager_b.getRate.return_value = 10
        mgrs = [manager_b]

        # Execute "manager status ManagerA"
        with mock.patch.object(HTTPCommand, 'execute', return_value=mgrs) as m:
            self.manager_command.execute(synergy_url="", args=mock_parser.args)

        # Check the executed call when we did "manager status"
        m.assert_called_once_with(
            "/synergy/status",
            {"manager": ["ManagerB"]})

        # Check the data when we call tabulate
        headers = ["manager", "status", "rate (min)"]
        table = [["ManagerB", "DOWN", 10]]
        mock_tabulate.assert_called_once_with(
            table,
            headers,
            tablefmt="fancy_grid")

    @mock.patch('synergy.client.command.tabulate')
    def test_execute_start_manager(self, mock_tabulate):
        """Check the CLI output of "manager start ManagerA"."""
        # Mock the parser call
        mock_parser = mock.Mock()
        mock_parser.args.command = "start"
        mock_parser.args.manager = "ManagerA"

        # Mock a manager
        manager_a = mock.Mock()
        manager_a.getName.return_value = "ManagerA"
        manager_a.getStatus.return_value = "RUNNING"
        manager_a.get.return_value = "started successfully"
        manager_a.getRate.return_value = 1
        mgrs = manager_a

        # Execute "manager start ManagerA"
        with mock.patch.object(HTTPCommand, 'execute', return_value=mgrs) as m:
            self.manager_command.execute(synergy_url='', args=mock_parser.args)

        # Check the executed call to "manager start ManagerA"
        m.assert_called_once_with(
            "/synergy/start",
            {"manager": "ManagerA"})

        # Check the data when we call tabulate
        headers = ["manager", "status", "rate (min)"]
        table = [["ManagerA", "RUNNING (started successfully)", 1]]
        mock_tabulate.assert_called_once_with(
            table,
            headers,
            tablefmt="fancy_grid")

    @mock.patch('synergy.client.command.tabulate')
    def test_execute_stop_manager(self, mock_tabulate):
        """Check the CLI output of "manager stop ManagerA"."""
        # Mock the parser call
        mock_parser = mock.Mock()
        mock_parser.args.command = "stop"
        mock_parser.args.manager = "ManagerA"

        # Mock a manager
        manager_a = mock.Mock()
        manager_a.getName.return_value = "ManagerA"
        manager_a.getStatus.return_value = "ACTIVE"
        manager_a.get.return_value = "stopped successfully"
        manager_a.getRate.return_value = 1
        mgrs = manager_a

        # Execute "manager stop ManagerA"
        with mock.patch.object(HTTPCommand, 'execute', return_value=mgrs) as m:
            self.manager_command.execute(synergy_url='', args=mock_parser.args)

        # Check the executed call to "manager stop ManagerA"
        m.assert_called_once_with(
            "/synergy/stop",
            {"manager": "ManagerA"})

        # Check the data when we call tabulate
        headers = ["manager", "status", "rate (min)"]
        table = [["ManagerA", "ACTIVE (stopped successfully)", 1]]
        mock_tabulate.assert_called_once_with(
            table,
            headers,
            tablefmt="fancy_grid")
