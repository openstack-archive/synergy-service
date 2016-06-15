import eventlet
import json
import logging
import logging.handlers
import os
import sys

from cgi import escape
from cgi import parse_qs
from pkg_resources import iter_entry_points

try:
    from oslo_config import cfg
except ImportError:
    from oslo.config import cfg

from synergy.common import config
from synergy.common import service
from synergy.common import wsgi

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
LOG = None
MANAGER_ENTRY_POINT = "synergy.managers"  # used to discover Synergy managers


def setLogger(name):
    """Configure the given logger with Synergy logging configuration.

    Note:
    This function should only be used when entering Synergy by the main()
    function. Otherwise you may run into issues due to logging to protected
    files.
    """
    # create a logging format
    formatter = logging.Formatter(CONF.Logger.formatter)

    log_dir = os.path.dirname(CONF.Logger.filename)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(
        CONF.Logger.filename,
        maxBytes=CONF.Logger.maxBytes,
        backupCount=CONF.Logger.backupCount)

    handler.setFormatter(formatter)

    # set logger level
    logger = logging.getLogger(name)
    logger.propagate = False

    try:
        logger.setLevel(cfg.CONF.Logger.level)
    except ValueError:  # wrong level, we default to INFO
        logger.setLevel(logging.INFO)

    logger.addHandler(handler)


class Synergy(service.Service):
    """Service object for binaries running on hosts.

    A service takes a manager and enables rpc by listening to queues based
    on topic. It also periodically runs tasks on the manager and reports
    it state to the database services table.
    """

    def __init__(self, *args, **kwargs):
        super(Synergy, self).__init__("Synergy")

        self.managers = {}

        for entry in iter_entry_points(MANAGER_ENTRY_POINT):
            LOG.info("loading manager %r", entry.name)

            try:
                CONF.register_opts(config.manager_opts, group=entry.name)

                manager_class = entry.load()

                manager_obj = manager_class(*args, **kwargs)
                LOG.info("manager instance %r created!", entry.name)

                manager_obj.setAutoStart(CONF.get(entry.name).autostart)
                manager_obj.setRate(CONF.get(entry.name).rate)

                self.managers[manager_obj.getName()] = manager_obj

                CONF.register_opts(manager_obj.getOptions(), group=entry.name)
            except Exception as ex:
                LOG.error("Exception has occured", exc_info=1)

                LOG.error("manager %r instantiation error: %s"
                          % (entry.name, ex))

                raise Exception("manager %r instantiation error: %s"
                                % (entry.name, ex))

        for name, manager in self.managers.items():
            manager.managers = self.managers

            try:
                LOG.info("initializing the %r manager" % (manager.getName()))

                manager.setup()

                LOG.info("manager %r initialized!" % (manager.getName()))
            except Exception as ex:
                LOG.error("Exception has occured", exc_info=1)

                LOG.error("manager %r instantiation error: %s" % (name, ex))
                self.managers[manager.getName()].setStatus("ERROR")
                raise ex

        self.saved_args, self.saved_kwargs = args, kwargs

    def listManagers(self, environ, start_response):
        result = []

        for name, manager in self.managers.items():
            result.append(name)

        start_response("200 OK", [("Content-Type", "text/html")])
        return ["%s" % json.dumps(result)]

    def getManagerStatus(self, environ, start_response):
        manager_list = None
        result = {}

        query = environ.get("QUERY_STRING", None)

        if query:
            parameters = parse_qs(query)

            if "manager" in parameters:
                if isinstance(parameters['manager'], (list, tuple)):
                    manager_list = parameters['manager']
                else:
                    manager_list = [parameters['manager']]
            else:
                manager_list = self.managers.keys()
        else:
            manager_list = self.managers.keys()

        for manager_name in manager_list:
            manager_name = escape(manager_name)

            if manager_name in self.managers:
                result[manager_name] = self.managers[manager_name].getStatus()

        if len(manager_list) == 1 and len(result) == 0:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["manager %r not found!" % manager_list[0]]

        start_response("200 OK", [("Content-Type", "text/html")])
        return ["%s" % json.dumps(result)]

    def executeCommand(self, environ, start_response):
        manager_name = None
        command = None

        query = environ.get("QUERY_STRING", None)

        if not query:
            start_response("400 BAD REQUEST", [("Content-Type", "text/plain")])
            return ["bad request"]

        parameters = parse_qs(query)
        LOG.debug("execute command: parameters=%s" % parameters)

        if "manager" not in parameters:
            start_response("400 BAD REQUEST", [("Content-Type", "text/plain")])
            return ["manager not specified!"]

        manager_name = escape(parameters['manager'][0])

        if manager_name not in self.managers:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["manager %r not found!" % manager_name]

        if "command" not in parameters:
            start_response("400 BAD REQUEST", [("Content-Type", "text/plain")])
            return ["bad request"]

        command = escape(parameters['command'][0])

        if "args" in parameters:
            manager_args = escape(parameters['args'][0])
            manager_args = manager_args.replace("'", "\"")
            manager_args = json.loads(manager_args)
        else:
            manager_args = {}

        manager = self.managers[manager_name]

        try:
            result = manager.execute(command=command, **manager_args)

            if not isinstance(result, dict):
                try:
                    result = result.toDict()
                except Exception:
                    result = result.__dict__

            LOG.debug("execute command: result=%s" % result)

            start_response("200 OK", [("Content-Type", "text/html")])
            return ["%s" % json.dumps(result)]
        except Exception as ex:
            LOG.debug("execute command: error=%s" % ex)
            start_response("500 INTERNAL SERVER ERROR",
                           [("Content-Type", "text/plain")])
            return ["error: %s" % ex]

    def startManager(self, environ, start_response):
        manager_list = None
        result = {}

        query = environ.get("QUERY_STRING", None)

        if not query:
            start_response("400 BAD REQUEST", [("Content-Type", "text/plain")])
            return ["bad request"]

        parameters = parse_qs(query)

        if "manager" not in parameters:
            start_response("400 BAD REQUEST", [("Content-Type", "text/plain")])
            return ["manager not specified!"]

        if isinstance(parameters['manager'], (list, tuple)):
            manager_list = parameters['manager']
        else:
            manager_list = [parameters['manager']]

        for manager_name in manager_list:
            manager_name = escape(manager_name)

            if manager_name not in self.managers:
                continue

            result[manager_name] = {}

            manager = self.managers[manager_name]

            if manager.getStatus() == "ACTIVE":
                LOG.info("starting the %r manager" % (manager_name))

                manager.resume()

                LOG.info("%r manager started! (rate=%s min)"
                         % (manager_name, manager.getRate()))

                result[manager_name]["status"] = "RUNNING"
                result[manager_name]["message"] = "started successfully"
            elif manager.getStatus() == "RUNNING":
                result[manager_name]["status"] = "RUNNING"
                result[manager_name]["message"] = "WARN: already started"
            elif manager.getStatus() == "ERROR":
                result[manager_name]["status"] = "ERROR"
                result[manager_name]["message"] = "wrong state"

        if len(manager_list) == 1 and len(result) == 0:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["manager %r not found!" % manager_list[0]]

        start_response("200 OK", [("Content-Type", "text/html")])
        return ["%s" % json.dumps(result)]

    def stopManager(self, environ, start_response):
        manager_list = None
        result = {}

        query = environ.get("QUERY_STRING", None)

        if not query:
            start_response("400 BAD REQUEST", [("Content-Type", "text/plain")])
            return ["bad request"]

        parameters = parse_qs(query)

        if "manager" not in parameters:
            start_response("400 BAD REQUEST", [("Content-Type", "text/plain")])
            return ["manager not specified!"]

        if isinstance(parameters['manager'], (list, tuple)):
            manager_list = parameters['manager']
        else:
            manager_list = [parameters['manager']]

        for manager_name in manager_list:
            manager_name = escape(manager_name)

            if manager_name not in self.managers:
                continue

            result[manager_name] = {}

            manager = self.managers[manager_name]

            if manager.getStatus() == "RUNNING":
                LOG.info("stopping the %r manager" % (manager_name))

                manager.pause()

                LOG.info("%r manager stopped!" % (manager_name))

                result[manager_name]["status"] = "ACTIVE"
                result[manager_name]["message"] = "stopped successfully"
            elif manager.getStatus() == "ACTIVE":
                result[manager_name]["status"] = "ACTIVE"
                result[manager_name]["message"] = "WARN: already stopped"
            elif manager.getStatus() == "ERROR":
                result[manager_name]["status"] = "ERROR"
                result[manager_name]["message"] = "wrong state"

        if len(manager_list) == 1 and len(result) == 0:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["manager %r not found!" % manager_list[0]]

        start_response("200 OK", [("Content-Type", "text/html")])
        return ["%s" % json.dumps(result)]

    def start(self):
        self.model_disconnected = False

        for name, manager in self.managers.items():
            if manager.getStatus() != "ERROR":
                try:
                    LOG.info("starting the %r manager" % (name))
                    manager.start()

                    LOG.info("%r manager started! (rate=%s min, status=%s)"
                             % (name, manager.getRate(), manager.getStatus()))
                except Exception as ex:
                    LOG.error("error occurred during the manager start %s"
                              % (ex))
                    manager.setStatus("ERROR")
                    raise ex

        self.wsgi_server = wsgi.Server(
            name="WSGI server",
            host_name=CONF.WSGI.host,
            host_port=CONF.WSGI.port,
            threads=CONF.WSGI.threads,
            use_ssl=CONF.WSGI.use_ssl,
            ssl_ca_file=CONF.WSGI.ssl_ca_file,
            ssl_cert_file=CONF.WSGI.ssl_cert_file,
            ssl_key_file=CONF.WSGI.ssl_key_file,
            max_header_line=CONF.WSGI.max_header_line,
            retry_until_window=CONF.WSGI.retry_until_window,
            tcp_keepidle=CONF.WSGI.tcp_keepidle,
            backlog=CONF.WSGI.backlog)

        self.wsgi_server.register(r'synergy/list', self.listManagers)
        self.wsgi_server.register(r'synergy/status', self.getManagerStatus)
        self.wsgi_server.register(r'synergy/execute', self.executeCommand)
        self.wsgi_server.register(r'synergy/start', self.startManager)
        self.wsgi_server.register(r'synergy/stop', self.stopManager)
        self.wsgi_server.start()

        LOG.info("STARTED!")
        self.wsgi_server.wait()

    def kill(self):
        """Destroy the service object in the datastore."""
        LOG.warn("killing service")
        self.stop()
        LOG.warn("Service killed")

    def stop(self):
        for name, manager in self.managers.items():
            LOG.info("destroying the %s manager" % (name))
            try:
                manager.setStatus("DESTROYED")
                manager.destroy()
                # manager.join()
                # LOG.info("%s manager destroyed" % (name))
            except Exception as ex:
                LOG.error("Exception has occured", exc_info=1)

                manager.setStatus("ERROR")
                LOG.error("error occurred during the manager destruction: %s"
                          % ex)

        if self.wsgi_server:
            self.wsgi_server.stop()

        LOG.info("STOPPED!")


def main():
    try:
        eventlet.monkey_patch(os=False)

        # the configuration will be into the cfg.CONF global data structure
        config.parseArgs(args=sys.argv[1:],
                         default_config_files=["/etc/synergy/synergy.conf"])

        if not cfg.CONF.config_file:
            sys.exit("ERROR: Unable to find configuration file via the "
                     "default search paths (~/.synergy/, ~/, /etc/synergy/"
                     ", /etc/) and the '--config-file' option!")

        setLogger(name="synergy")

        global LOG
        # LOG = logging.getLogger(None)

        LOG = logging.getLogger(__name__)
        LOG.info("Starting Synergy...")

        # set session ID to this process so we can kill group in sigterm
        # os.setsid()

        server = Synergy()

        # Configure logging for managers
        for manager in server.managers.values():
            setLogger(manager.__module__)

        server.start()

        LOG.info("Synergy started")
    except Exception as ex:
        LOG.error("unrecoverable error: %s" % ex)
