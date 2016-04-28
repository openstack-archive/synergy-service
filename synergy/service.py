import eventlet
import json
import sys

from cgi import escape
from cgi import parse_qs
from pkg_resources import iter_entry_points
from synergy.common import config
from synergy.common import log as logging
from synergy.common import serializer
from synergy.common import service
from synergy.common import wsgi

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
LOG = None
MANAGER_ENTRY_POINT = "synergy.managers"  # used to discover Synergy managers


class ManagerRPC(object):

    def __init__(self, managers):
        self.managers = managers

    def list(self, ctx, **args):
        result = []

        for name, manager in self.managers.items():
            result.append(name)

        return result

    def start(self, ctx, **args):
        manager_name = args.get("arg").get("manager", None)
        result = {}

        for name, manager in self.managers.items():
            if manager.getStatus() == "ACTIVE" \
               and (not manager_name or manager_name == name):
                LOG.info("starting the %s manager" % (name))
                try:
                    # self.managers[name].start()
                    self.managers[name].setStatus("RUNNING")
                    LOG.info("%s manager started" % (name))

                    result[name] = manager.getStatus()
                except Exception as ex:
                    self.managers[name].setStatus("ERROR")
                    LOG.error("error occurred during the manager start-up %s"
                              % (ex))

                    result[name] = manager.getStatus()
                    pass

        return result

    def stop(self, ctx, **args):
        manager_name = args.get("arg").get("manager", None)
        result = {}

        for name, manager in self.managers.items():
            if manager.getStatus() == "RUNNING" \
               and (not manager_name or manager_name == name):
                LOG.info("stopping the %s manager" % (name))
                try:
                    # self.managers[name].stop()
                    self.managers[name].setStatus("ACTIVE")
                    LOG.info("%s manager stopped" % (name))

                    result[name] = manager.getStatus()
                except Exception as ex:
                    self.managers[name].setStatus("ERROR")
                    LOG.error("error occurred during the manager stop %s"
                              % (ex))

                    result[name] = manager.getStatus()
                    pass

        return result

    def execute(self, ctx, **args):
        manager_name = args.get("arg").get("manager", None)
        command = args.get("arg").get("command", None)
        result = {}

        if not manager_name:
            result["error"] = "manager name not defined!"

        if not command:
            result["error"] = "command not defined!"

        if manager_name in self.managers:
            manager = self.managers[manager_name]
            manager.execute(cmd=command)
            result["command"] = "OK"

        return result

    def status(self, ctx, **args):
        manager_name = args.get("arg").get("manager", None)
        result = {}

        for name, manager in self.managers.items():
            if not manager_name or manager_name == name:
                result[name] = manager.getStatus()

        return result


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
                """
                found = False

                try:
                    CONF.get(entry.name)
                    found = True
                except Exception as ex:
                    LOG.info("missing section [%s] in synergy.conf for manager"
                             " %r: using the default values"
                             % (entry.name, entry.name))
                """

                CONF.register_opts(config.manager_opts, group=entry.name)

                manager_conf = CONF.get(entry.name)
                manager_class = entry.load()

                manager_obj = manager_class(*args, **kwargs)
                LOG.info("manager instance %r created!", entry.name)

                manager_obj.setAutoStart(manager_conf.autostart)
                manager_obj.setRate(manager_conf.rate)

                self.managers[manager_obj.getName()] = manager_obj

                CONF.register_opts(manager_obj.getOptions(), group=entry.name)
            except Exception as ex:
                LOG.error("Exception has occured", exc_info=1)

                LOG.error("manager %r instantiation error: %s"
                          % (entry.name, ex))
                self.managers[manager_obj.getName()].setStatus("ERROR")

                raise Exception("manager %r instantiation error: %s"
                                % (entry.name, ex))

        for name, manager in self.managers.items():
            manager.managers = self.managers

            try:
                manager.setup()
                manager.setStatus("ACTIVE")

                LOG.info("manager '%s' initialized!" % (manager.getName()))
            except Exception as ex:
                LOG.error("manager '%s' instantiation error: %s" % (name, ex))
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

                for manager in manager_list:
                    escape(manager)

        for name, manager in self.managers.items():
            if not manager_list or name in manager_list:
                result[name] = manager.getStatus()

        if manager_list and len(manager_list) == 1 and len(result) == 0:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["manager %r not found!" % manager_list[0]]
        else:
            start_response("200 OK", [("Content-Type", "text/html")])
            return ["%s" % json.dumps(result)]

    def executeCommand(self, environ, start_response):
        manager_name = None
        command = None

        synergySerializer = serializer.SynergySerializer()
        query = environ.get("QUERY_STRING", None)
        # LOG.info("QUERY_STRING %s" % query)
        if query:
            parameters = parse_qs(query)

            if "manager" in parameters:
                manager_name = escape(parameters['manager'][0])

            if "command" in parameters:
                command_string = escape(parameters['command'][0])
                command_string = command_string.replace("'", "\"")
                entity = json.loads(command_string)
                command = synergySerializer.deserialize_entity(context=None,
                                                               entity=entity)

        if not query or not manager_name or not command:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["wrong query"]

        if manager_name in self.managers:
            manager = self.managers[manager_name]
            try:
                manager.execute(cmd=command)
                result = synergySerializer.serialize_entity(context=None,
                                                            entity=command)
                # LOG.info("command result %s" % result)

                start_response("200 OK", [("Content-Type", "text/html")])
                return ["%s" % json.dumps(result)]
            except Exception as ex:
                LOG.info("executeCommand error: %s" % ex)
                start_response("404 NOT FOUND",
                               [("Content-Type", "text/plain")])
                return ["error: %s" % ex]
        else:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["manager %r not found!" % manager_name]

    def startManager(self, environ, start_response):
        manager_list = None
        result = {}

        # synergySerializer = serializer.SynergySerializer()
        query = environ.get("QUERY_STRING", None)

        if query:
            parameters = parse_qs(query)

            if "manager" in parameters:
                if isinstance(parameters['manager'], (list, tuple)):
                    manager_list = parameters['manager']
                else:
                    manager_list = [parameters['manager']]

                for manager in manager_list:
                    escape(manager)

        for name, manager in self.managers.items():
            if not manager_list or name in manager_list:
                result[name] = {}

                if manager.getStatus() == "ACTIVE":
                    LOG.info("starting the %r manager" % (name))
                    try:
                        # self.managers[name].start()
                        self.managers[name].setStatus("RUNNING")
                        LOG.info("%r manager started!" % (name))

                        result[name]["message"] = "started successfully"
                    except Exception as ex:
                        self.managers[name].setStatus("ERROR")
                        LOG.error("error occurred during the manager start-up"
                                  "%s" % (ex))

                        result[name]["message"] = "ERROR: %s" % ex
                        pass
                else:
                    result[name]["message"] = "WARN: already started"

                result[name]["status"] = manager.getStatus()

        if manager_list and len(manager_list) == 1 and len(result) == 0:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["manager %r not found!" % manager_list[0]]
        else:
            start_response("200 OK", [("Content-Type", "text/html")])
            return ["%s" % json.dumps(result)]

    def stopManager(self, environ, start_response):
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

                for manager in manager_list:
                    escape(manager)

        for name, manager in self.managers.items():
            if not manager_list or name in manager_list:
                result[name] = {}

                if manager.getStatus() == "RUNNING":
                    LOG.info("stopping the %r manager" % (name))
                    try:
                        # self.managers[name].stop()
                        self.managers[name].setStatus("ACTIVE")
                        LOG.info("%r manager stopped!" % (name))

                        result[name]["message"] = "stopped successfully"
                    except Exception as ex:
                        self.managers[name].setStatus("ERROR")
                        LOG.error("error occurred during the manager stop: %s"
                                  % (ex))

                        result[name]["message"] = "ERROR: %s" % ex
                        pass
                else:
                    result[name]["message"] = "WARN: already stopped"

                result[name]["status"] = manager.getStatus()

        if manager_list and len(manager_list) == 1 and len(result) == 0:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["manager %r not found!" % manager_list[0]]
        else:
            start_response("200 OK", [("Content-Type", "text/html")])
            return ["%s" % json.dumps(result)]

    def start(self):
        self.model_disconnected = False

        for name, manager in self.managers.items():
            if manager.getStatus() != "ERROR" and manager.isAutoStart():
                try:
                    LOG.info("starting the %r manager" % (name))
                    manager.start()
                    manager.setStatus("RUNNING")
                    LOG.info("%r manager started! (rate=%s min)"
                             % (name, manager.getRate()))
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
        config.parse_args(args=sys.argv[1:],
                          default_config_files=["/etc/synergy/synergy.conf"])

        if not cfg.CONF.config_file:
            sys.exit("ERROR: Unable to find configuration file via the "
                     "default search paths (~/.synergy/, ~/, /etc/synergy/"
                     ", /etc/) and the '--config-file' option!")

        global LOG
        # LOG = logging.getLogger(None)

        LOG = logging.getLogger(__name__)
        LOG.info("Starting Synergy...")

        # set session ID to this process so we can kill group in sigterm
        # os.setsid()

        server = Synergy()
        server.start()

        LOG.info("Synergy started")
    except Exception as ex:
        LOG.error("unrecoverable error: %s" % ex)
