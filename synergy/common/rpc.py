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

try:
    from oslo_config import cfg
except ImportError:
    from oslo.config import cfg

try:
    import oslo_messaging as messaging
except ImportError:
    import oslo.messaging as messaging

from synergy.common import log as logging

CONF = cfg.CONF
TRANSPORT = None
NOTIFIER = None

ALLOWED_EXMODS = []
EXTRA_EXMODS = []

LOG = logging.getLogger(__name__)


def init(conf):
    global TRANSPORT, NOTIFIER

    LOG.info(">>>>>>>> rpc init")
    try:

        transport_url = 'rabbit://guest:RABBIT_PASS@10.64.21.5:5672/'
        TRANSPORT = messaging.get_transport(conf, transport_url)
    except Exception as ex:
        LOG.error("rpc init error %s" % ex)
        raise ex

    LOG.info(">>>>>>>> rpc init done")

    # NOTIFIER = oslo_messaging.Notifier(TRANSPORT, serializer=serializer)


def cleanup():
    global TRANSPORT, NOTIFIER
    assert TRANSPORT is not None
    assert NOTIFIER is not None
    TRANSPORT.cleanup()
    TRANSPORT = NOTIFIER = None


def setDefaults(control_exchange):
    messaging.set_transport_defaults(control_exchange)


def getTransportURL(url_str=None):
    return messaging.TransportURL.parse(CONF, url_str, TRANSPORT_ALIASES)


def getClient(target, version_cap=None, serializer=None):
    assert TRANSPORT is not None

    # if not serializer:
    #    serializer = ser.RequestContextSerializer()

    return messaging.RPCClient(
        TRANSPORT, target, version_cap=version_cap, serializer=serializer)


def getServer(target, endpoints, serializer=None):
    assert TRANSPORT is not None

    # if serializer is None:
    #    serializer = ser.RequestContextSerializer()

    return messaging.get_rpc_server(
        TRANSPORT, target, endpoints, executor="eventlet",
        serializer=serializer)


# def getNotificationListener(service=None, host=None, publisher_id=None):
def getNotificationListener(target, endpoints):
    assert TRANSPORT is not None
    # assert NOTIFIER is not None
    """
    if not publisher_id:
        publisher_id = "%s.%s" % (service, host or CONF.host)
    """
    # return NOTIFIER.prepare(publisher_id=publisher_id)

    return messaging.get_notification_listener(
        TRANSPORT, target, endpoints, allow_requeue=True, executor="eventlet")
