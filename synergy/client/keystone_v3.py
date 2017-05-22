import json
import os.path
import requests

from datetime import datetime
from synergy.client.exception import SynergyError


__author__ = "Lisa Zangrando"
__email__ = "lisa.zangrando[AT]pd.infn.it"
__copyright__ = """Copyright (c) 2015 INFN - INDIGO-DataCloud
All Rights Reserved

Licensed under the Apache License, Version 2.0;
you may not use this file except in compliance with the
License. You may obtain a copy of the License at:

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied.
See the License for the specific language governing
permissions and limitations under the License."""


class Token(object):

    def __init__(self, token, data):
        self.id = token

        data = data["token"]
        self.roles = data["roles"]
        self.catalog = data["catalog"]
        self.issued_at = datetime.strptime(data["issued_at"],
                                           "%Y-%m-%dT%H:%M:%S.%fZ")
        self.expires_at = datetime.strptime(data["expires_at"],
                                            "%Y-%m-%dT%H:%M:%S.%fZ")
        self.project = data["project"]
        self.user = data["user"]

        if "extras" in data:
            self.extras = data["extras"]

    def getCatalog(self):
        return self.catalog

    def getExpiration(self):
        return self.expires_at

    def getId(self):
        return self.id

    def getExtras(self):
        return self.extras

    def getProject(self):
        return self.project

    def getRoles(self):
        return self.roles

    def getUser(self):
        return self.user

    def isAdmin(self):
        if not self.roles:
            return False

        for role in self.roles:
            if role["name"] == "admin":
                return True

        return False

    def issuedAt(self):
        return self.issued_at

    def isExpired(self):
        return self.getExpiration() < datetime.utcnow()

    def save(self, filename):
        # save to file
        with open(filename, 'w') as f:
            token = {}
            token["catalog"] = self.catalog
            token["extras"] = self.extras
            token["user"] = self.user
            token["project"] = self.project
            token["roles"] = self.roles
            token["roles"] = self.roles
            token["issued_at"] = self.issued_at.isoformat()
            token["expires_at"] = self.expires_at.isoformat()

            data = {"id": self.id, "token": token}

            json.dump(data, f)

    @classmethod
    def load(cls, filename):
        if not os.path.isfile(".auth_token"):
            return None

        # load from file:
        with open(filename, 'r') as f:
            try:
                data = json.load(f)
                return Token(data["id"], data)
            # if the file is empty the ValueError will be thrown
            except ValueError as ex:
                raise SynergyError(ex)

    def isotime(self, at=None, subsecond=False):
        """Stringify time in ISO 8601 format."""
        if not at:
            at = datetime.utcnow()

        if not subsecond:
            st = at.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            st = at.strftime('%Y-%m-%dT%H:%M:%S.%f')

        if at.tzinfo:
            tz = at.tzinfo.tzname(None)
        else:
            tz = 'UTC'

        st += ('Z' if tz == 'UTC' else tz)
        return st


class KeystoneClient(object):

    def __init__(self, auth_url, username, password, user_domain_id=None,
                 user_domain_name="default", project_id=None,
                 project_name=None, project_domain_id=None,
                 project_domain_name="default", timeout=None, ca_cert=None):
        self.auth_url = auth_url
        self.username = username
        self.password = password
        self.user_domain_id = user_domain_id
        self.user_domain_name = user_domain_name
        self.project_id = project_id
        self.project_name = project_name
        self.project_domain_id = project_domain_id
        self.project_domain_name = project_domain_name
        self.timeout = timeout
        self.token = None
        self.ca_cert = ca_cert

    def authenticate(self):
        if self.token is not None:
            if self.token.isExpired():
                try:
                    self.deleteToken(self.token.getId())
                except requests.exceptions.HTTPError:
                    pass
            else:
                return

        headers = {"Content-Type": "application/json",
                   "Accept": "application/json",
                   "User-Agent": "python-novaclient"}

        user_domain = {}
        if self.user_domain_id is not None:
            user_domain["id"] = self.user_domain_id
        else:
            user_domain["name"] = self.user_domain_name

        project_domain = {}
        if self.project_domain_id is not None:
            project_domain["id"] = self.project_domain_id
        else:
            project_domain["name"] = self.project_domain_name

        identity = {"methods": ["password"],
                    "password": {"user": {"name": self.username,
                                          "domain": user_domain,
                                          "password": self.password}}}

        data = {"auth": {}}
        data["auth"]["identity"] = identity

        if self.project_name:
            data["auth"]["scope"] = {"project": {"name": self.project_name,
                                                 "domain": project_domain}}

        if self.project_id:
            data["auth"]["scope"] = {"project": {"id": self.project_id,
                                                 "domain": project_domain}}

        response = requests.post(url=self.auth_url + "/auth/tokens",
                                 headers=headers,
                                 data=json.dumps(data),
                                 timeout=self.timeout,
                                 verify=self.ca_cert)

        if response.status_code != requests.codes.ok:
            response.raise_for_status()

        if not response.text:
            raise SynergyError("authentication failed!")

        token_subject = response.headers["X-Subject-Token"]
        token_data = response.json()

        self.token = Token(token_subject, token_data)

        return self.token

    def getToken(self):
        return self.token

    def getService(self, name):
        for service in self.token.getCatalog():
            if service["name"] == name:
                return service

        raise SynergyError("service %s not found!" % name)

    def getEndpoint(self, name, interface="public"):
        service = self.getService(name)

        for endpoint in service["endpoints"]:
            if endpoint["interface"] == interface:
                return endpoint

        raise SynergyError("endpoint for service %s not found!" % name)
