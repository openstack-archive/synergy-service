try:
    import oslo_messaging
except ImportError:
    import oslo.messaging as oslo_messaging

from synergy.common import context as ctx
from synergy.common import utils


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


class SynergyObject(object):
    """Base class and object factory.

    This forms the base of all objects that can be remoted or instantiated
    via RPC. Simply defining a class that inherits from this base class
    will make it remotely instantiatable. Objects should implement the
    necessary "get" classmethod routines as well as "set" object methods
    as appropriate.
    """
    VERSION = "1.0"

    def __init__(self, name=None):
        self.attributes = {}

        if name:
            self.attributes["name"] = name

    def getName(self):
        return self.attributes["name"]

    def setName(self, name):
        self.attributes["name"] = name

    def get(self, field=None):
        return self.attributes.get(field, None)

    def set(self, field, value):
        self.attributes[field] = value

    def setContext(self, context):
        self.context = context

    def setAttributes(self, attributes):
        if attributes:
            self.attributes = attributes

    @classmethod
    def deserialize(cls, context, entity):
        if "synergy_object.namespace" not in entity:
            raise Exception("synergy_object.namespace nof defined!")

        if "synergy_object.name" not in entity:
            raise Exception("synergy_object.name nof defined!")

        if "synergy_object.version" not in entity:
            raise Exception("synergy_object.version nof defined!")

        if entity["synergy_object.namespace"] != 'synergy':
            raise Exception("unsupported object objtype='%s.%s"
                            % (entity["synergy_object.namespace"],
                               entity["synergy_object.name"]))

        objName = entity['synergy_object.name']
        # objVer = entity['synergy_object.version']
        objClass = utils.import_class(objName)

        # objInstance = objClass(context=context, data=entity)

        objInstance = objClass(name=None)
        objInstance.setContext(context)
        objInstance.setAttributes(entity)

        return objInstance

    def serialize(self):
        name = self.__class__.__module__ + "." + self.__class__.__name__
        self.attributes['synergy_object.name'] = name
        self.attributes['synergy_object.version'] = self.VERSION
        self.attributes['synergy_object.namespace'] = 'synergy'

        return self.attributes
    """
    def log(self):
        for key, value in self.attributes.items():
            LOG.info("%s = %s" % (key, value))
    """


class SynergySerializer(oslo_messaging.Serializer):
    def __init__(self):
        super(SynergySerializer, self).__init__()

    def serialize_entity(self, context, entity):
        if not entity:
            return entity

        if isinstance(entity, SynergyObject):
            entity = entity.serialize()
        elif isinstance(entity, dict):
            result = {}

            for key, value in entity.items():
                result[key] = self.serialize_entity(context, value)

            entity = result

        return entity

    def deserialize_entity(self, context, entity):
        if isinstance(entity, dict):
            if 'synergy_object.name' in entity:
                entity = SynergyObject.deserialize(context, entity)
            else:
                result = {}

                for key, value in entity.items():
                    result[key] = self.deserialize_entity(context, value)

                entity = result

        return entity

    def serialize_context(self, context):
        return context.toDict()

    def deserialize_context(self, context):
        return ctx.RequestContext.fromDict(context)


class RequestContextSerializer(oslo_messaging.Serializer):
    def __init__(self):
        pass

    def serialize_entity(self, context, entity):
        return entity

    def deserialize_entity(self, context, entity):
        return entity

    def serialize_context(self, context):
        return context.toDict()

    def deserialize_context(self, context):
        return ctx.RequestContext.fromDict(context)
