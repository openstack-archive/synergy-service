import json
import requests

from synergy.common import utils
from tabulate import tabulate


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

    def objectHookHandler(self, parsed_dict):
        if "synergy_object" in parsed_dict:
            synergy_object = parsed_dict["synergy_object"]
            try:
                objClass = utils.import_class(synergy_object["name"])

                objInstance = objClass()
                return objInstance.deserialize(parsed_dict)
            except Exception as ex:
                print(ex)
                raise ex
        else:
            return parsed_dict

    def execute(self, synergy_url, payload=None):
        request = requests.get(synergy_url, params=payload)

        if request.status_code != requests.codes.ok:
            # print(request.reason)
            # print(request.status_code)
            request.raise_for_status()

        self.results = request.json()

        try:
            return json.loads(request.text, object_hook=self.objectHookHandler)
        except Exception:
            return request.json()

    def getResults(self):
        return self.results


class ManagerCommand(HTTPCommand):

    def __init__(self):
        super(ManagerCommand, self).__init__("Manager")

    def configureParser(self, subparser):
        manager_parser = subparser.add_parser('manager')
        manager_parsers = manager_parser.add_subparsers(dest="command")

        manager_parsers.add_parser(
            "list", add_help=True, help="list the managers")

        status_parser = manager_parsers.add_parser(
            "status", add_help=True, help="show the managers status")

        status_parser.add_argument(
            "manager", nargs='*', help="the managers list")

        start_parser = manager_parsers.add_parser(
            "start", add_help=True, help="start the manager")

        start_parser.add_argument(
            "manager", nargs='+', help="the managers list")

        stop_parser = manager_parsers.add_parser(
            "stop", add_help=True, help="stop the manager")

        stop_parser.add_argument(
            "manager", nargs='+', help="the managers list")

    def execute(self, synergy_url, args=None):
        table = []
        headers = []
        url = synergy_url

        if args.command == "list":
            headers.append("manager")
            url += "/synergy/list"

            managers = super(ManagerCommand, self).execute(url)

            for manager in managers:
                table.append([manager.getName()])
        else:
            headers.append("manager")
            headers.append("status")
            headers.append("rate (min)")
            url += "/synergy/" + args.command

            managers = super(ManagerCommand, self).execute(
                url, {"manager": args.manager})

            if args.command == "status":
                for manager in managers:
                    table.append([manager.getName(),
                                  manager.getStatus(),
                                  manager.getRate()])
            else:
                headers.append("details")

                for manager in managers:
                    msg = manager.get("message")

                    table.append([manager.getName(),
                                  manager.getStatus() + " (%s)" % msg,
                                  manager.getRate()])

        print(tabulate(table, headers, tablefmt="fancy_grid"))


class ExecuteCommand(HTTPCommand):

    def __init__(self, name):
        super(ExecuteCommand, self).__init__(name)

    def execute(self, synergy_url, manager, command, args=None):
        if args is None:
            args = {}

        url = synergy_url + "/synergy/execute"

        payload = {"manager": manager,
                   "command": command,
                   "args": json.dumps(args)}

        return super(ExecuteCommand, self).execute(url, payload)
