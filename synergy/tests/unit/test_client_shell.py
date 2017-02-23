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
Test the shell.

"""

import mock

from argparse import Namespace
from synergy.client import keystone_v3
from synergy.client.shell import main
from synergy.tests import base


class TestHTTPCommand(base.TestCase):

    def setUp(self):
        super(TestHTTPCommand, self).setUp()

    @mock.patch('synergy.client.command.ManagerCommand.execute')
    @mock.patch('sys.argv')
    def test_create_keystone_client(self, mock_argv, _mock_httpcmd):
        """Check success when all parameters are filled."""
        args = [
            '--os-username', 'username',
            '--os-password', 'password',
            '--os-user-domain-id', 'user_domain_id',
            '--os-user-domain-name', 'user_domain_name',
            '--os-project-name', 'project_name',
            '--os-project-domain-id', 'project_domain_id',
            '--os-project-domain-name', 'project_domain_name',
            '--os-auth-token-cache',
            '--os-auth-url', 'auth_url',
            '--os-cacert', 'cacert',
            'manager', 'list']
        mock_argv.__getitem__.return_value = args

        with mock.patch.object(keystone_v3, 'KeystoneClient') as m:
            main()
        m.assert_called_once_with(
            auth_url='auth_url',
            username='username',
            password='password',
            ca_cert='cacert',
            user_domain_id='user_domain_id',
            user_domain_name='user_domain_name',
            project_name='project_name',
            project_domain_id='project_domain_id',
            project_domain_name='project_domain_name')

    @mock.patch('synergy.client.command.ManagerCommand.execute')
    @mock.patch('sys.argv')
    def test_no_username(self, mock_argv, _mock_httpcmd):
        """CLI should exit if no username is specified."""
        args = [
            '--os-password', 'password',
            '--os-user-domain-id', 'user_domain_id',
            '--os-user-domain-name', 'user_domain_name',
            '--os-project-name', 'project_name',
            '--os-project-domain-id', 'project_domain_id',
            '--os-project-domain-name', 'project_domain_name',
            '--os-auth-token-cache',
            '--os-auth-url', 'auth_url',
            '--os-cacert', 'cacert',
            'manager', 'list']
        mock_argv.__getitem__.return_value = args

        with mock.patch('sys.exit') as m:
            main()
        m.assert_called_once_with(1)

    @mock.patch('synergy.client.command.ManagerCommand.execute')
    @mock.patch('sys.argv')
    def test_no_password(self, mock_argv, _mock_httpcmd):
        """CLI should exit if no password is specified."""
        args = [
            '--os-username', 'username',
            '--os-user-domain-id', 'user_domain_id',
            '--os-user-domain-name', 'user_domain_name',
            '--os-project-name', 'project_name',
            '--os-project-domain-id', 'project_domain_id',
            '--os-project-domain-name', 'project_domain_name',
            '--os-auth-token-cache',
            '--os-auth-url', 'auth_url',
            '--os-cacert', 'cacert',
            'manager', 'list']
        mock_argv.__getitem__.return_value = args

        with mock.patch('sys.exit') as m:
            main()
        m.assert_called_once_with(1)

    @mock.patch('synergy.client.command.ManagerCommand.execute')
    @mock.patch('sys.argv')
    def test_no_project_name(self, mock_argv, _mock_httpcmd):
        """CLI should exit if no project name is specified."""
        args = [
            '--os-username', 'username',
            '--os-password', 'password',
            '--os-user-domain-id', 'user_domain_id',
            '--os-user-domain-name', 'user_domain_name',
            '--os-project-domain-id', 'project_domain_id',
            '--os-project-domain-name', 'project_domain_name',
            '--os-auth-token-cache',
            '--os-auth-url', 'auth_url',
            '--os-cacert', 'cacert',
            'manager', 'list']
        mock_argv.__getitem__.return_value = args

        with mock.patch('sys.exit') as m:
            main()
        m.assert_called_once_with(1)

    @mock.patch('synergy.client.command.ManagerCommand.execute')
    @mock.patch('sys.argv')
    def test_no_auth_url(self, mock_argv, _mock_httpcmd):
        """CLI should exit if no auth URL is specified."""
        args = [
            '--os-username', 'username',
            '--os-password', 'password',
            '--os-user-domain-id', 'user_domain_id',
            '--os-user-domain-name', 'user_domain_name',
            '--os-project-name', 'project_name',
            '--os-project-domain-id', 'project_domain_id',
            '--os-project-domain-name', 'project_domain_name',
            '--os-auth-token-cache',
            '--os-cacert', 'cacert',
            'manager', 'list']
        mock_argv.__getitem__.return_value = args

        with mock.patch('sys.exit') as m:
            main()
        m.assert_called_once_with(1)

    @mock.patch('synergy.client.command.ManagerCommand.execute')
    @mock.patch('sys.argv')
    def test_minimum_parameters(self, mock_argv, _mock_httpcmd):
        """CLI should not exit when the required parameters are filled."""
        args = [
            '--os-username', 'username',
            '--os-password', 'password',
            '--os-project-name', 'project_name',
            '--os-auth-url', 'auth_url',
            'manager', 'list']
        mock_argv.__getitem__.return_value = args

        # Bypass HTTP call
        with mock.patch.object(keystone_v3, 'KeystoneClient'):
            with mock.patch('sys.exit') as sys_exit:
                main()
        sys_exit.assert_not_called()

    @mock.patch('synergy.client.command.ManagerCommand.execute')
    @mock.patch('sys.argv')
    def test_auth_token_cache_valid(self, mock_argv, _mock_httpcmd):
        """Token should be loaded from cache."""
        args = [
            '--os-username', 'username',
            '--os-password', 'password',
            '--os-user-domain-id', 'user_domain_id',
            '--os-user-domain-name', 'user_domain_name',
            '--os-project-name', 'project_name',
            '--os-project-domain-id', 'project_domain_id',
            '--os-project-domain-name', 'project_domain_name',
            '--os-auth-token-cache',
            '--os-auth-url', 'auth_url',
            '--os-cacert', 'cacert',
            'manager', 'list']
        mock_argv.__getitem__.return_value = args

        with mock.patch.object(keystone_v3, 'KeystoneClient'):
            with mock.patch.object(keystone_v3.Token, 'load') as token_load:
                main()
        token_load.assert_called_once_with('.auth_token')

    @mock.patch('synergy.client.command.ManagerCommand.execute')
    @mock.patch('sys.argv')
    def test_bypass_url(self, mock_argv, mock_httpcmd):
        """Token should be loaded from cache."""
        args = [
            '--bypass-url', 'bypass_url',
            'manager', 'list']
        mock_argv.__getitem__.return_value = args

        with mock.patch.object(keystone_v3, 'KeystoneClient'):
            main()

        ns = Namespace(
            bypass_url='bypass_url',
            command='list',
            command_name='manager',
            debug=False,
            os_auth_token_cache=False,
            os_auth_url=None,
            os_cacert=None,
            os_password=None,
            os_project_domain_id=None,
            os_project_domain_name=None,
            os_project_id=None,
            os_project_name=None,
            os_user_domain_id=None,
            os_user_domain_name=None,
            os_username=None)
        mock_httpcmd.assert_called_once_with("bypass_url", ns)
