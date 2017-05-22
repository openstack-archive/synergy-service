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

auth_opts = [
    cfg.StrOpt("plugin", default="noauth", help="the authorization plugin"),
    cfg.StrOpt("policy_file", default="policy.json", help="the plucy file"),
]

wsgi_opts = [
    cfg.StrOpt("host", default="localhost",
               help="Address to bind the server"),
    cfg.IntOpt("port", default=8051,
               help="The port on which the server will listen"),
    cfg.IntOpt("threads", default=1000),
    cfg.IntOpt("backlog", default=4096,
               help="Number of backlog requests to configure the socket with"),
    cfg.IntOpt("tcp_keepidle", default=600,
               help="Sets the value of TCP_KEEPIDLE in seconds for each server"
                    " socket (not supported on OS X)"),
    cfg.IntOpt("retry_until_window", default=30,
               help="Number of seconds to keep retrying to listen"),
    cfg.IntOpt("max_header_line", default=16384,
               help="Max header line to accommodate large tokens"),
    cfg.BoolOpt("use_ssl", default=False,
                help="Enable SSL on the API server"),
    cfg.StrOpt("ssl_ca_file", default=None,
               help="CA certificate file to use to verify connecting clients"),
    cfg.StrOpt("ssl_cert_file", default=None,
               help="The certificate file"),
    cfg.StrOpt("ssl_key_file", default=None,
               help="The private key file")
]

logger_opts = [
    cfg.StrOpt("filename", default="/tmp/synergy.log",
               required=True),
    cfg.StrOpt("level", default="INFO", required=False),
    cfg.IntOpt("maxBytes", default=1048576),
    cfg.IntOpt("backupCount", default=100),
    cfg.StrOpt("formatter",
               default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
               required=False)
]

manager_opts = [
    cfg.BoolOpt("autostart", default=False),
    cfg.IntOpt("rate", default=60)
]

cfg.CONF.register_opts(wsgi_opts, group="WSGI")
cfg.CONF.register_opts(logger_opts, group="Logger")
cfg.CONF.register_opts(auth_opts, group="Authorization")


def parseArgs(args=None, usage=None, default_config_files=None):
    cfg.CONF(args=args,
             project='synergy',
             version="1.0",
             usage=usage,
             default_config_files=default_config_files)
