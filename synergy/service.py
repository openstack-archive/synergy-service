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

import sys
import eventlet
import json

from cgi import parse_qs
from cgi import escape
from pkg_resources import iter_entry_points

try:
    from oslo_config import cfg
except ImportError:
    from oslo.config import cfg

from synergy.common import config
# from synergy.common import rpc
from synergy.common import serializer
from synergy.common import service
from synergy.common import wsgi
from synergy.common import log as logging

__author__ = "Lisa Zangrando"
__email__ = "lisa.zangrando[AT]pd.infn.it"

CONF = cfg.CONF
LOG = None
MANAGER_ENTRY_POINT = "synergy.managers"  # used to discover synergy managers


# keystone user-create --name synergy --tenant services --pass pippo12345
# keystone user-role-add --user synergy --tenant services --role admin
# keystone service-create --name synergy --type management

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
            if manager.getStatus() == "ACTIVE" and (not manager_name or manager_name == name):
                LOG.info("starting the %s manager" % name)
                try:
                    # self.managers[name].start()
                    self.managers[name].setStatus("RUNNING")
                    LOG.info("%s manager started" % name)

                    result[name] = manager.getStatus()
                except Exception as ex:
                    self.managers[name].setStatus("ERROR")
                    LOG.error("error occurred during the manager start-up %s" % ex)

                    result[name] = manager.getStatus()
                    pass

        return result

    def stop(self, ctx, **args):
        manager_name = args.get("arg").get("manager", None)
        result = {}

        for name, manager in self.managers.items():
            if (manager.getStatus() == "RUNNING") and (not manager_name or manager_name == name):
                LOG.info("stopping the %s manager" % name)
                try:
                    # self.managers[name].stop()
                    self.managers[name].setStatus("ACTIVE")
                    LOG.info("%s manager stopped" % name)

                    result[name] = manager.getStatus()
                except Exception:
                    self.managers[name].setStatus("ERROR")
                    LOG.error("error occurred during the manager stop %s" % ex)

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

    # def __init__(self, host, topic, exchange, managers, *args, **kwargs):
    def __init__(self, *args, **kwargs):
        super(Synergy, self).__init__("Synergy")

        self.managers = {}

        for manager_name in self._get_manager_names():
            try:
                CONF.register_opts(config.manager_opts, group=manager_name)

                manager_entry_point = next(iter_entry_points(MANAGER_ENTRY_POINT, CONF.get(manager_name).name))
                manager_class = manager_entry_point.load()

                manager_obj = manager_class(*args, **kwargs)
                manager_obj.setAutoStart(CONF.get(manager_name).autostart)
                manager_obj.setRate(CONF.get(manager_name).rate)

                self.managers[manager_obj.getName()] = manager_obj

                CONF.register_opts(manager_obj.getOptions(), group=manager_name)
            except Exception as ex:
                LOG.error("Exception has occured", exc_info=1)

                LOG.error("manager '%s' instantiation error: %s" % (manager_name, ex))
                self.managers[manager_obj.getName()].setStatus("ERROR")
                raise Exception("manager '%s' instantiation error: %s" % (manager_name, ex))

        for name, manager in self.managers.items():
            try:
                if len(CONF.get(name).dependences) == 0:
                    manager.setup()
                    manager.setStatus("ACTIVE")

                    LOG.info("manager '%s' initialized" % (manager.getName()))
            except Exception as ex:
                LOG.error("manager '%s' instantiation error: %s" % (name, ex))
                self.managers[manager.getName()].setStatus("ERROR")
                raise ex

        done = False
        retry_count = 1

        while not done and retry_count >= 0:
            done = True
            retry_count -= 1

            for name, manager in self.managers.items():
                try:
                    if len(CONF.get(name).dependences) > 0:
                        for dependence in CONF.get(name).dependences:
                            if dependence in manager.dependences:
                                continue
                            elif dependence in self.managers:
                                manager_dep = self.managers[dependence]

                                if manager_dep.getStatus() == "ACTIVE":
                                    manager.dependences[dependence] = manager_dep
                                    LOG.info("added dependence '%s' to '%s'" % (dependence, name))
                                elif manager_dep.getStatus() == "ERROR":
                                    raise Exception("dependence '%s' has ERROR state!" % dependence)
                                elif name in CONF.get(dependence).dependences:
                                    raise Exception(
                                        "found cyclic dependence: %s <-> %s" % (name, manager_dep.getName()))
                            else:
                                raise Exception("dependence '%s' not found for '%s'!" % (dependence, name))

                        if len(manager.dependences) == len(CONF.get(name).dependences):
                            manager.setup()
                            manager.setStatus("ACTIVE")

                            LOG.info("manager initialized: %s" % (manager.getName()))
                        else:
                            done = False
                except Exception as ex:
                    LOG.error("manager '%s' instantiation error: %s" % (name, ex))
                    self.managers[manager.getName()].setStatus("ERROR")
                    raise ex

        self.rpcserver = None
        self.saved_args, self.saved_kwargs = args, kwargs

    @staticmethod
    def _get_manager_names():
        manager_names = []
        try:
            main_config_file = cfg.CONF.config_file[0]
        except IndexError:
            LOG.warning("No default config file set, cannot get manager names.")
        else:
            sections = {}
            cfg.ConfigParser(main_config_file, sections).parse()

            for manager_name, manager_info in sections.items():
                if 'type' in manager_info and 'manager' in manager_info['type']:
                    manager_names.append(manager_name)

        return manager_names

    def listManagers(self, environ, start_response):
        result = []

        for name, manager in self.managers.items():
            result.append(name)

        start_response("200 OK", [("Content-Type", "text/html")])
        return ["%s" % json.dumps(result)]

    def getManagerStatus(self, environ, start_response):
        manager_list = None
        result = {}

        # LOG.info(">>>>>>>>>>>>> args=%s" % environ)

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
            return ["manager '%s' not found!" % manager_list[0]]
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
                command = synergySerializer.deserialize_entity(context=None, entity=entity)

        if not query or not manager_name or not command:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["wrong query"]

        if manager_name in self.managers:
            manager = self.managers[manager_name]
            try:
                manager.execute(cmd=command)
                result = synergySerializer.serialize_entity(context=None, entity=command)
                # LOG.info("command result %s" % result)

                start_response("200 OK", [("Content-Type", "text/html")])
                return ["%s" % json.dumps(result)]
            except Exception as ex:
                LOG.info("executeCommand error: %s" % ex)
                start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
                return ["error: %s" % ex]
        else:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["manager '%s' not found!" % manager_name]

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
                    LOG.info("starting the %s manager" % name)
                    try:
                        # self.managers[name].start()
                        self.managers[name].setStatus("RUNNING")
                        LOG.info("%s manager started" % name)

                        result[name]["message"] = "started successfully"
                    except Exception as ex:
                        self.managers[name].setStatus("ERROR")
                        LOG.error("error occurred during the manager start-up %s" % ex)

                        result[name]["message"] = "ERROR: %s" % ex
                        pass
                else:
                    result[name]["message"] = "WARN: already started"

                result[name]["status"] = manager.getStatus()

        if manager_list and len(manager_list) == 1 and len(result) == 0:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["manager '%s' not found!" % manager_list[0]]
        else:
            start_response("200 OK", [("Content-Type", "text/html")])
            return ["%s" % json.dumps(result)]

    def stopManager(self, environ, start_response):
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

                if manager.getStatus() == "RUNNING":
                    LOG.info("stopping the %s manager" % name)
                    try:
                        # self.managers[name].stop()
                        self.managers[name].setStatus("ACTIVE")
                        LOG.info("%s manager stopped" % name)

                        result[name]["message"] = "stopped successfully"
                    except Exception as ex:
                        self.managers[name].setStatus("ERROR")
                        LOG.error("error occurred during the manager stop: %s" % ex)

                        result[name]["message"] = "ERROR: %s" % ex
                        pass
                else:
                    result[name]["message"] = "WARN: already stopped"

                result[name]["status"] = manager.getStatus()

        if manager_list and len(manager_list) == 1 and len(result) == 0:
            start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
            return ["manager '%s' not found!" % manager_list[0]]
        else:
            start_response("200 OK", [("Content-Type", "text/html")])
            return ["%s" % json.dumps(result)]

    def start(self):
        # self.basic_config_check()
        self.model_disconnected = False

        for name, manager in self.managers.items():
            if manager.getStatus() != "ERROR" and manager.isAutoStart():
                try:
                    LOG.info("starting the %s manager" % name)
                    manager.start()
                    manager.setStatus("RUNNING")
                    LOG.info("%s manager started" % name)
                except Exception as ex:
                    LOG.error("error occurred during the manager start %s" % ex)
                    manager.setStatus("ERROR")
                    raise ex

        # LOG.info("Creating RPC server for service exchange=%s topic=%s host=%s" % (self.exchange, self.topic, self.host))
        # target = messaging.Target(topic=self.topic, server=self.host)
        # endpoints = [ ManagerRPC(self.managers) ]

        """
        LOG.info("initializing RPC")
        rpc.init(CONF)
        LOG.info("initializing RPC done!")
        """
        # self.rpcserver = rpc.getServer(target, endpoints, synergySerializer)
        # self.rpcserver.start()
        # self.rpcserver.wait()

        # quiet = True

        self.wsgi_server = wsgi.Server(name="WSGI server",
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

        # wsgi.Server(name, threads=1000, use_ssl=False, ssl_ca_file=None, ssl_cert_file=None, ssl_key_file=None, max_header_line=16384, retry_until_window=30, tcp_keepidle=600, backlog=4096):

        self.wsgi_server.register(r'^$', wsgi.index)
        # self.wsgi_server.register('hello', wsgi.hello)
        self.wsgi_server.register(r'synergy/list', self.listManagers)
        self.wsgi_server.register(r'synergy/status', self.getManagerStatus)
        self.wsgi_server.register(r'synergy/execute', self.executeCommand)
        self.wsgi_server.register(r'synergy/start', self.startManager)
        self.wsgi_server.register(r'synergy/stop', self.stopManager)
        # self.wsgi_server.register(r'hello/?$', wsgi.hello)
        # self.wsgi_server.register(r'hello/(.+)$', wsgi.hello)
        # self.wsgi_server.register(r'v2/(.+)$', wsgi.printenv)
        self.wsgi_server.start()

        LOG.info("STARTED!")
        self.wsgi_server.wait()

    def kill(self):
        """Destroy the service object in the datastore."""
        LOG.warn("killing service")
        self.stop()
        LOG.warn("Service killed")

    def stop(self):
        """
        try:
            print ("destroying rpcserver")
            self.rpcserver.stop()
            self.rpcserver.wait()
            LOG.info("rpcserver destroyed")
        except Exception as ex:
            LOG.exception("error occurred during shutdown: %s" % ex)
        """

        for name, manager in self.managers.items():
            LOG.info("destroying the %s manager" % name)
            try:
                manager.setStatus("DESTROYED")
                manager.destroy()
                # manager.join()
                # LOG.info("%s manager destroyed" % (name))
            except Exception as ex:
                manager.setStatus("ERROR")
                LOG.error("error occurred during the manager destruction: %s" % ex)

        if self.wsgi_server:
            self.wsgi_server.stop()

        LOG.info("STOPPED!")


def main():
    try:
        eventlet.monkey_patch(os=False)

        # the configuration will be read into the cfg.CONF global data structure
        config.parse_args(args=sys.argv[1:], default_config_files=["/etc/synergy/synergy.conf"])

        if not cfg.CONF.config_file:
            sys.exit(
                "ERROR: Unable to find configuration file via the default search paths (~/.synergy/, ~/, /etc/synergy/, /etc/) and the '--config-file' option!")

        global LOG
        # LOG = logging.getLogger(None)

        LOG = logging.getLogger(__name__)
        LOG.info("Starting Synergy...")

        # set session ID to this process so we can kill group in sigterm handler
        # os.setsid()
        server = Synergy()
        server.start()

        LOG.info("Synergy started")
    except Exception as ex:
        LOG.error("unrecoverable error: %s" % ex)
