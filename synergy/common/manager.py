from threading import Condition
from threading import Event
from threading import Thread

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


class Manager(Thread):

    def __init__(self, name):
        super(Manager, self).__init__()
        self.setDaemon(True)
        self.stop_event = Event()
        self.config_opts = []
        self.condition = Condition()
        self.name = name
        self.status = "CREATED"
        self.autostart = False
        self.rate = -1
        self.paused = True  # start out paused
        self.managers = {}

    def execute(self, command, *args, **kargs):
        raise NotImplementedError

    def task(self):
        raise NotImplementedError

    def doOnEvent(self, event_type, *args, **kargs):
        raise NotImplementedError

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
        self.paused = not self.autostart

    def getRate(self):
        return self.rate

    def setRate(self, rate):
        self.rate = rate

    def setup(self):
        """Manager initialization

        Hook to do additional manager initialization when one requests
        the service be started. This is called before any service record
        is created.
        Child classes should override this method.
        """
        raise NotImplementedError

    def destroy(self):
        raise NotImplementedError

    def getStatus(self):
        return self.status

    def setStatus(self, status):
        with self.condition:
            self.status = status

            self.condition.notifyAll()

    def stop(self):
        if self.isAlive():
            # set event to signal thread to terminate
            self.stop_event.set()
            self.resume()
            # block calling thread until thread really has terminated
            self.join()

    def pause(self):
        with self.condition:
            self.paused = True
            self.condition.notifyAll()

    def resume(self):
        with self.condition:
            self.paused = False
            self.condition.notifyAll()

    def run(self):
        while not self.stop_event.isSet():
            with self.condition:
                if self.paused:
                    self.status = "ACTIVE"
                    self.condition.wait()
                else:
                    self.status = "RUNNING"

                    try:
                        self.task()
                        self.condition.wait(self.rate * 60)
                    except Exception as ex:
                        print("task %r: %s" % (self.name, ex))
