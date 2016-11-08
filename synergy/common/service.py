import logging
import os
import signal
import sys

from oslo_config import cfg


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

CONF = cfg.CONF
LOG = logging.getLogger(__name__)
SIGTERM_SENT = False


class Service(object):
    def __init__(self, name):
        self.name = name
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGINT, self.sigterm_handler)

    def sigterm_handler(self, signum, frame):
        LOG.debug("Signal handler called with signal=%s" % signum)

        global SIGTERM_SENT
        if not SIGTERM_SENT:
            LOG.info("Shutting down %s" % self.name)
            SIGTERM_SENT = True
            self.stop()
            os.killpg(0, signal.SIGTERM)

        sys.exit()

    def getName(self):
        return self.name

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def wait(self):
        raise NotImplementedError

    def restart(self):
        # Reload config files and restart service
        CONF.reload_config_files()
        self.stop()
        self.start()
