from synergy.common import serializer

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


class Command(serializer.SynergyObject):
    VERSION = "1.0"

    def __init__(self, name):
        super(Command, self).__init__(name)

    def getParameters(self):
        parameters = self.get("parameters")

        if parameters is None:
            self.set("parameters", {})

        return self.get("parameters")

    def addParameter(self, name, value):
        self.getParameters()[name] = value

    def getParameter(self, name):
        return self.getParameters().get(name, None)

    def setParameters(self, parameters):
        self.set("parameters", parameters)

    def getResults(self):
        result = self.get("result")

        if not result:
            self.set("result", {})

        return self.get("result")

    def addResult(self, name, value):
        self.getResults()[name] = value

    def getResult(self, name):
        return self.getResults().get(name, None)

    def setResults(self, data):
        self.set("result", data)
