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
Test the Trust class.

"""

import mock

from datetime import datetime
from synergy.client.keystone_v3 import Trust
from synergy.tests import base


class TestTrust(base.TestCase):

    def setUp(self):
        super(TestTrust, self).setUp()

    def test_trust_no_expires_at(self):
        data = {
            "trust": {
                "id": 1,
                "impersonation": False,
                "roles_links": "some links",
                "trustor_user_id": 0,
                "trustee_user_id": 1,
                "links": "some links",
                "roles": "roll roll roll",
                "remaining_uses": 10,
                "expires_at": None,
                "project_id": 46}}
        trust = Trust(data)

        self.assertEqual(1, trust.getId())
        self.assertEqual(False, trust.isImpersonations())
        self.assertEqual("some links", trust.getRolesLinks())
        self.assertEqual(0, trust.getTrustorUserId())
        self.assertEqual(1, trust.getTrusteeUserId())
        self.assertEqual("some links", trust.getlinks())
        self.assertEqual(46, trust.getProjectId())
        self.assertEqual("roll roll roll", trust.getRoles())
        self.assertEqual(10, trust.getRemainingUses())
        self.assertIsNone(trust.getExpiration())
        self.assertEqual(False, trust.isExpired())

    def test_trust_not_expired(self):
        mock_utcnow = datetime(2000, 1, 1)
        data = {
            "trust": {
                "id": 1,
                "impersonation": False,
                "roles_links": "some links",
                "trustor_user_id": 0,
                "trustee_user_id": 1,
                "links": "some links",
                "roles": "roll roll roll",
                "remaining_uses": 10,
                "expires_at": "1900-01-01T00:00:00.000Z",
                "project_id": 46}}
        trust = Trust(data)

        self.assertEqual(datetime(1900, 1, 1, 0, 0, 0), trust.getExpiration())
        with mock.patch('datetime.datetime') as m:
            m.utcnow.return_value = mock_utcnow
            self.assertEqual(True, trust.isExpired())

    def test_trust_expired(self):
        mock_utcnow = datetime(2099, 1, 1)
        data = {
            "trust": {
                "id": 1,
                "impersonation": False,
                "roles_links": "some links",
                "trustor_user_id": 0,
                "trustee_user_id": 1,
                "links": "some links",
                "roles": "roll roll roll",
                "remaining_uses": 10,
                "expires_at": "2099-01-01T00:00:00.000Z",
                "project_id": 46}}
        trust = Trust(data)

        self.assertEqual(datetime(2099, 1, 1, 0, 0, 0), trust.getExpiration())
        with mock.patch('datetime.datetime') as m:
            m.utcnow.return_value = mock_utcnow
            self.assertEqual(False, trust.isExpired())
