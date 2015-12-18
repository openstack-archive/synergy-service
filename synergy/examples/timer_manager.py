# Copyright (c) 2014 INFN - "Istituto Nazionale di Fisica Nucleare" - Italy
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

__author__ = "Lisa Zangrando"
__email__ = "lisa.zangrando[AT]pd.infn.it"


import time

from synergy.common import manager
from synergy.common import log as logging


LOG = logging.getLogger(__name__)


class TimerManager(manager.Manager):

    def __init__(self):
        super(TimerManager, self).__init__(name="TimerManager", autostart=False, rate=1)


    def setup(self):
        LOG.info("%s setup invoked!" % (self.name))


    def execute(self, cmd):
        LOG.info("%s execute invoked!" % (self.name))
        LOG.info("command name=%s" % (cmd.getName()))

    """
    def start(self):
        LOG.info("%s start invoked!" % (self.name))


    def stop(self):
        LOG.info("%s stop invoked!" % (self.name))
    """

    def destroy(self):
        LOG.info("%s destroy invoked!" % (self.name))


    def task(self):
        localtime = time.asctime(time.localtime(time.time()))
        LOG.info("Local current time: %s" % (localtime))

