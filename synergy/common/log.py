import logging
import logging.handlers

try:
    from oslo_config import cfg
except ImportError:
    from oslo.config import cfg

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
loggers = {}


def getLogger(name="unknown"):
    global loggers

    if loggers.get(name):
        return loggers.get(name)

    else:
        logger = logging.getLogger(name)

        if CONF.Logger.level == "DEBUG":
            logger.setLevel(logging.DEBUG)
        elif CONF.Logger.level == "INFO":
            logger.setLevel(logging.INFO)
        elif CONF.Logger.level == "WARNING":
            logger.setLevel(logging.WARNING)
        elif CONF.Logger.level == "ERROR":
            logger.setLevel(logging.ERROR)
        elif CONF.Logger.level == "CRITICAL":
            logger.setLevel(logging.CRITICAL)
        else:
            logger.setLevel(logging.INFO)

        # create a logging format
        formatter = logging.Formatter(CONF.Logger.formatter)

        # Add the log message handler to the logger
        handler = logging.handlers.RotatingFileHandler(
            CONF.Logger.filename,
            maxBytes=CONF.Logger.maxBytes,
            backupCount=CONF.Logger.backupCount)

        handler.setFormatter(formatter)

        logger.addHandler(handler)

        loggers[name] = logger

        return logger
