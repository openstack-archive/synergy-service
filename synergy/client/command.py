import json
import requests

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


class HTTPCommand(object):

    def __init__(self, name):
        self.name = name

    def getName(self):
        return self.name

    def configureParser(self, subparser):
        raise NotImplementedError("not implemented!")

    def log(self):
        raise NotImplementedError("not implemented!")

    def sendRequest(self, synergy_url, payload=None):
        request = requests.get(synergy_url, params=payload)

        if request.status_code != requests.codes.ok:
            # print(request.reason)
            # print(request.status_code)
            request.raise_for_status()

        self.results = request.json()

        return request

    def getResults(self):
        return self.results


class List(HTTPCommand):

    def __init__(self):
        super(List, self).__init__("list")

    def configureParser(self, subparser):
        subparser.add_parser("list", add_help=True, help="list the managers")

    def sendRequest(self, synergy_url, args=None):
        super(List, self).sendRequest(synergy_url + "/synergy/list")

    def log(self):
        results = self.getResults()

        max_project_id = max(len(max(results, key=len)), len("manager"))
        separator_str = "-" * (max_project_id + 4) + "\n"
        format_str = "| {0:%ss} |\n" % (max_project_id)

        msg = separator_str
        msg += format_str.format("manager")
        msg += separator_str

        for manager in results:
            msg += format_str.format(manager)

        msg += separator_str
        print(msg)


class Start(HTTPCommand):

    def __init__(self):
        super(Start, self).__init__("start")

    def configureParser(self, subparser):
        parser = subparser.add_parser("start",
                                      add_help=True,
                                      help="start the managers")

        parser.add_argument("manager", help="the manager to be started")

    def sendRequest(self, synergy_url, args):
        super(Start, self).sendRequest(synergy_url + "/synergy/start",
                                       {"manager": args.manager})

    def log(self):
        results = self.getResults()

        max_manager = max(len(max(results.keys(), key=len)), len("manager"))

        max_status = len("status")
        max_msg = len("message")

        for result in results.values():
            max_status = max(len(str(result["status"])), max_status)
            max_msg = max(len(str(result["message"])), max_msg)

        separator_str = "-" * (max_manager + max_status + max_msg + 10) + "\n"

        format_str = "| {0:%ss} | {1:%ss} | {2:%ss} |\n" % (max_manager,
                                                            max_status,
                                                            max_msg)

        msg = separator_str
        msg += format_str.format("manager", "status", "message")
        msg += separator_str

        for manager, values in results.items():
            msg += format_str.format(manager,
                                     values["status"],
                                     values["message"])

        msg += separator_str
        print(msg)


class Stop(HTTPCommand):

    def __init__(self):
        super(Stop, self).__init__("stop")

    def configureParser(self, subparser):
        parser = subparser.add_parser("stop",
                                      add_help=True,
                                      help="stop the managers")

        parser.add_argument("manager", help="the manager to be stopped")

    def sendRequest(self, synergy_url, args):
        super(Stop, self).sendRequest(synergy_url + "/synergy/stop",
                                      {"manager": args.manager})

    def log(self):
        results = self.getResults()

        max_manager = max(len(max(results.keys(), key=len)), len("manager"))
        max_status = len("status")
        max_msg = len("message")

        for result in results.values():
            max_status = max(len(str(result["status"])), max_status)
            max_msg = max(len(str(result["message"])), max_msg)

        separator_str = "-" * (max_manager + max_status + max_msg + 10) + "\n"
        format_str = "| {0:%ss} | {1:%ss} | {2:%ss} |\n" % (max_manager,
                                                            max_status,
                                                            max_msg)

        msg = separator_str
        msg += format_str.format("manager", "status", "message")
        msg += separator_str

        for manager, values in results.items():
            msg += format_str.format(manager,
                                     values["status"],
                                     values["message"])

        msg += separator_str
        print(msg)


class Status(HTTPCommand):

    def __init__(self):
        super(Status, self).__init__("status")

    def configureParser(self, subparser):
        parser = subparser.add_parser("status",
                                      add_help=True,
                                      help="retrieve the manager's status")

        parser.add_argument("manager", nargs='*', help="the managers list")

    def sendRequest(self, synergy_url, args):
        super(Status, self).sendRequest(synergy_url + "/synergy/status",
                                        {"manager": args.manager})

    def log(self):
        results = self.getResults()

        max_project_id = max(len(max(results.keys(), key=len)), len("manager"))
        max_value = max(len(max(results.values(), key=len)), len("status"))
        separator_str = "-" * (max_project_id + max_value + 7) + "\n"
        format_str = "| {0:%ss} | {1:%ss} |\n" % (max_project_id, max_value)

        msg = separator_str
        msg += format_str.format("manager", "status")
        msg += separator_str

        for manager, status in results.items():
            msg += format_str.format(manager, status)

        msg += separator_str
        print(msg)


class Execute(HTTPCommand):

    def __init__(self, name):
        super(Execute, self).__init__(name)

    def sendRequest(self, synergy_url, manager, command, args=None):
        if args is None:
            args = {}

        payload = {"manager": manager,
                   "command": command,
                   "args": json.dumps(args)}

        super(Execute, self).sendRequest(synergy_url + "/synergy/execute",
                                         payload)
