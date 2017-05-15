import errno
import eventlet
import logging
import os
import re
import socket
import ssl
import time

from eventlet import greenio as eventlet_greenio
from eventlet import wsgi as eventlet_wsgi
from synergy.exception import SynergyError
from sys import exc_info
from traceback import format_tb


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

LOG = logging.getLogger(__name__)


class Dispatcher(object):
    """Dispatcher

    The main WSGI application. Dispatch the current request to
    the functions from above and store the regular expression
    captures in the WSGI environment as `myapp.url_args` so that
    the functions from above can access the url placeholders.
    If nothing matches call the `not_found` function.
    """

    def __init__(self):
        self.actions = {}

    def register(self, action, callback):
        self.actions[action] = callback

    def unregister(self, action):
        del self.actions[action]

    def __call__(self, environ, start_response):
        """Call the application can catch exceptions."""
        appiter = None
        # just call the application and send the output back unchanged
        # but catch exceptions

        path = environ.get('PATH_INFO', '').lstrip('/')
        application = None

        for regex, callback in self.actions.items():
            match = re.search(regex, path)
            if match is not None:
                environ['myapp.url_args'] = match.groups()
                application = callback
                break

        if application is not None:
            try:
                self.appiter = callback(environ, start_response)
                for item in self.appiter:
                    yield item
            # if an exception occours we get the exception information and
            # prepare a traceback we can render
            except Exception:
                e_type, e_value, tb = exc_info()
                traceback = ['Traceback (most recent call last):']
                traceback += format_tb(tb)
                traceback.append('%s: %s' % (e_type.__name__, e_value))
                # we might have not a stated response by now.
                # Try to start one with the status
                # code 500 or ignore an raised exception if the application
                # already started one.
                try:
                    start_response("500 INTERNAL SERVER ERROR",
                                   [('Content-Type', 'text/plain')])
                except Exception:
                    pass
                yield '\n'.join(traceback)

            # wsgi applications might have a close function.
            # If it exists it *must* be called.
            if hasattr(appiter, 'close'):
                self.appiter.close()
        else:
            """Called if no applations matches."""
            try:
                start_response("404 NOT FOUND",
                               [('Content-Type', 'text/plain')])
            except Exception:
                pass
            yield "Not Found"


class WSGILog(object):
    """A thin wrapper that responds to `write` and logs."""

    def __init__(self, logger, level=20):
        self.logger = logger
        self.level = level

    def write(self, msg):
        self.logger.log(self.level, msg.rstrip())


class Server(object):
    """Server class to manage multiple WSGI sockets and applications."""

    def __init__(self, name, host_name, host_port=8051, threads=1000,
                 application=None, use_ssl=False, ssl_ca_file=None,
                 ssl_cert_file=None, ssl_key_file=None, max_header_line=16384,
                 retry_until_window=30, tcp_keepidle=600, backlog=4096):

        """Parameters

        name: the server's name
        host_name: the host's name
        host_port:
        application:
        backlog: number of backlog requests to configure the socket with
        tcp_keepidle: sets the value of TCP_KEEPIDLE in seconds for each server
        socket. Not supported on OS X
        retry_until_window: number of seconds to keep retrying to listen
        max_header_line: max header line to accommodate large tokens
        use_ssl: enable SSL on the API server
        ssl_ca_file: CA certificate file to use to verify connecting clients
        ssl_cert_file: the certificate file
        ssl_key_file: the private key file
        """

        # Raise the default from 8192 to accommodate large tokens
        eventlet_wsgi.MAX_HEADER_LINE = max_header_line

        self.name = name
        self.host_name = host_name
        self.host_port = host_port
        self.application = application
        self.threads = threads
        self.socket = None
        self.use_ssl = use_ssl
        self.tcp_keepidle = tcp_keepidle
        self.backlog = backlog
        self.retry_until_window = retry_until_window
        self.running = False
        self.dispatcher = Dispatcher()

        if not application:
            self.application = self.dispatcher

        if use_ssl:
            if not os.path.exists(ssl_cert_file):
                raise RuntimeError("Unable to find ssl_cert_file: %s"
                                   % ssl_cert_file)

            if not os.path.exists(ssl_key_file):
                raise RuntimeError("Unable to find ssl_key_file : %s"
                                   % ssl_key_file)

            # ssl_ca_file is optional
            if ssl_ca_file and not os.path.exists(ssl_ca_file):
                raise RuntimeError("Unable to find ssl_ca_file: %s"
                                   % ssl_ca_file)

            self.ssl_kwargs = {
                'server_side': True,
                'certfile': ssl_cert_file,
                'keyfile': ssl_key_file,
                'cert_reqs': ssl.CERT_NONE,
            }

            if ssl_ca_file:
                self.ssl_kwargs['ca_certs'] = ssl_ca_file
                self.ssl_kwargs['cert_reqs'] = ssl.CERT_REQUIRED

    def register(self, action, callback):
        self.dispatcher.register(action, callback)

    def unregister(self, action):
        self.dispatcher.unregister(action)

    def start(self):
        """Run a WSGI server with the given application.

        :param application: The application to be run in the WSGI server
        :param port: Port to bind to if none is specified in conf
        """

        pgid = os.getpid()
        try:
            # NOTE(flaper87): Make sure this process
            # runs in its own process group.
            os.setpgid(pgid, pgid)
        except OSError:
            pgid = 0

        try:
            info = socket.getaddrinfo(self.host_name,
                                      self.host_port,
                                      socket.AF_UNSPEC,
                                      socket.SOCK_STREAM)[0]
            family = info[0]
            bind_addr = info[-1]
        except Exception as ex:
            raise SynergyError("Unable to listen on %s:%s: %s"
                               % (self.host_name, self.host_port, ex))

        retry_until = time.time() + self.retry_until_window
        exception = None

        while not self.socket and time.time() < retry_until:
            try:
                self.socket = eventlet.listen(bind_addr,
                                              backlog=self.backlog,
                                              family=family)
                if self.use_ssl:
                    self.socket = ssl.wrap_socket(self.socket,
                                                  **self.ssl_kwargs)

                if self.use_ssl:
                    ssl.wrap_socket(self.sock, **self.ssl_kwarg)

            except socket.error as ex:
                exception = ex
                LOG.error("Unable to listen on %s:%s: %s"
                          % (self.host_name, self.host_port, ex))

                if ex.errno == errno.EADDRINUSE:
                    retry_until = 0
                    eventlet.sleep(0.1)
                    break

        if exception is not None:
            raise exception

        if not self.socket:
            raise RuntimeError("Could not bind to %s:%s after trying for %d s"
                               % (self.host_name, self.host_port,
                                  self.retry_until_window))

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # sockets can hang around forever without keepalive
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # This option isn't available in the OS X version of eventlet
        if hasattr(socket, 'TCP_KEEPIDLE'):
            self.socket.setsockopt(socket.IPPROTO_TCP,
                                   socket.TCP_KEEPIDLE,
                                   self.tcp_keepidle)

        os.umask(0o27)  # ensure files are created with the correct privileges

        self.pool = eventlet.GreenPool(self.threads)
        self.pool.spawn_n(self._single_run, self.application, self.socket)

        self.running = True

    def isRunning(self):
        return self.running

    def stop(self):
        LOG.info("shutting down: requests left: %s", self.pool.running())
        self.running = False
        self.pool.resize(0)
        # self.pool.waitall()

        if self.socket:
            eventlet_greenio.shutdown_safe(self.socket)
            self.socket.close()

        self.running = False

    def wait(self):
        """Wait until all servers have completed running"""
        try:
            self.pool.waitall()
        except KeyboardInterrupt:
            pass

    def _single_run(self, application, sock):
        """Start a WSGI server in a new green thread."""
        LOG.info("Starting single process server")
        eventlet_wsgi.server(sock, application,
                             custom_pool=self.pool,
                             log=WSGILog(LOG),
                             debug=False)
