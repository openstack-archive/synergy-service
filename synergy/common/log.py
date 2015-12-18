# Copyright (c) 2015 INFN - INDIGO-DataCloud
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unl        os.system("apt-get -y install ess required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import logging.handlers

try:
    from oslo_config import cfg
except ImportError:
    from oslo.config import cfg

__author__ = "Lisa Zangrando"
__email__ = "lisa.zangrando[AT]pd.infn.it"

loggers = {}


def getLogger(name="unknown"):
    global loggers

    if loggers.get(name):
        return loggers.get(name)

    else:
        logger = logging.getLogger(name)

        if cfg.CONF.Logger.level == "DEBUG":
            logger.setLevel(logging.DEBUG)
        elif cfg.CONF.Logger.level == "INFO":
            logger.setLevel(logging.INFO)
        elif cfg.CONF.Logger.level == "WARNING":
            logger.setLevel(logging.WARNING)
        elif cfg.CONF.Logger.level == "ERROR":
            logger.setLevel(logging.ERROR)
        elif cfg.CONF.Logger.level == "CRITICAL":
            logger.setLevel(logging.CRITICAL)
        else:
            logger.setLevel(logging.INFO)

        # create a logging format
        formatter = logging.Formatter(cfg.CONF.Logger.formatter)

        # Add the log message handler to the logger
        handler = logging.handlers.RotatingFileHandler(cfg.CONF.Logger.filename, maxBytes=cfg.CONF.Logger.maxBytes,
                                                       backupCount=cfg.CONF.Logger.backupCount)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        loggers[name] = logger

        return logger
