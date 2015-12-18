from threading import Condition
from threading import Timer


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


class Manager(object):

    def __init__(self, name):
        self.config_opts = []
        self.condition = Condition()
        self.name = name
        self.status = "CREATED"
        self.autostart = False
        self.rate = -1
        self.timer = None
        self.is_running = False
        self.managers = {}

    def execute(self, command, *args, **kargs):
        pass

    def task(self):
        pass

    def doOnEvent(self, event_type, *args, **kargs):
        pass

    def getManagers(self):
        return self.managers

    def getManager(self, name):
        return self.managers.get(name, None)

    def notify(self, event_type="DEFAULT", manager_name=None, *args, **kargs):
        if manager_name is not None:
            if manager_name in self.managers:
                self.managers[manager_name].doOnEvent(event_type,
                                                      *args, **kargs)
        else:
            for manager in self.managers.values():
                if manager.getName() != manager_name:
                    manager.doOnEvent(event_type, *args, **kargs)

    def getName(self):
        return self.name

    def getOptions(self):
        return self.config_opts

    def isAutoStart(self):
        return self.autostart

    def setAutoStart(self, autostart):
        self.autostart = autostart

    def getRate(self):
        return self.rate

    def setRate(self, rate):
        if rate and rate > 0:
            self.rate = rate

    def setup(self):
        """Manager initialization

        Hook to do additional manager initialization when one requests
        the service be started. This is called before any service record
        is created.
        Child classes should override this method.
        """
        pass

    def destroy(self):
        pass

    def getStatus(self):
        return self.status

    def setStatus(self, status):
        with self.condition:
            self.status = status

            self.condition.notifyAll()
            # if self.status == "RUNNING":
            #     self.__task()

    """
    def __task(self):
        if self.rate:
            if self.status == "RUNNING":
                self.task()
                self.timer = Timer(self.rate, self.__task)
                self.timer.start()
            else:
                self.timer.cancel()
    """

    def start(self):
        if not self.rate:
            return

        if not self.is_running and self.rate > 0:
            self.timer = Timer(self.rate * 60, self._run)
            self.timer.start()
            self.is_running = True

    def _run(self):
        self.is_running = False
        self.start()

        if self.status == "RUNNING":
            self.task()

    def stop(self):
        self.timer.cancel()
        self.is_running = False

    def run(self):
        if not self.rate:
            return

        with self.condition:
            while self.status != "DESTROYED" and self.status != "ERROR":
                if self.status == "RUNNING":
                    self.task()

                    self.condition.wait(self.rate)
                else:
                    self.condition.wait()
