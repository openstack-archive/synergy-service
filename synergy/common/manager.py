# Copyright (c) 2015 INFN - INDIGO-DataCloud
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = "Lisa Zangrando"
__email__ = "lisa.zangrando[AT]pd.infn.it"

"""Base Manager class.
"""

from threading import Condition
from threading import Timer

# try:
#     from oslo_config import cfg
# except ImportError:
#     from oslo.config import cfg


# CONF = cfg.CONF
# CONF.import_opt('host', 'nova.netconf')

# LOG = logging.getLogger(__name__)

# class Manager(Thread):
class Manager(object):

    def __init__(self, name, autostart=True, rate=None):
        # super(Manager, self).__init__()

        # self.setDaemon(True)
        self.config_opts = []
        self.condition = Condition()
        self.name = name
        self.status = "CREATED"
        self.autostart = autostart
        self.rate = rate
        self.timer = None
        self.is_running = False
        self.dependences = {}

        if rate and rate > 0:
            self.rate = rate * 60.0

    def getDependences(self):
        return self.dependences

    def getDependence(self, name):
        if name in self.dependences:
            return self.dependences[name]
        else:
            return None

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
        self.rate = rate

    def setup(self):
        """Hook to do additional manager initiation

        This is called before any service record is created.

        Child classes should override this method.
        """
        pass

    def destroy(self):
        pass

    def getStatus(self):
        return self.status

    def setStatus(self, status):
        try:
            with self.condition:
                self.status = status

                self.condition.notifyAll()
                # if self.status == "RUNNING":
                #     self.__task()

        except Exception as ex:
            LOG.info("error %s" % ex)

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

    def execute(self, cmd):
        pass

    def task(self):
        pass

    def start(self):
        if not self.rate:
            return

        if not self.is_running:
            self.timer = Timer(self.rate, self._run)
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

    """
    def start(self):
        pass

    def stop(self):
        pass
    """

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
