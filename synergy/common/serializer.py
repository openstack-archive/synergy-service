from datetime import datetime
from json import JSONEncoder
from synergy.common import utils
from synergy.exception import SynergyError


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

    def __init__(self):
        super(SynergyObject, self).__init__()

        self.attributes = {}

    def getId(self):
        return self.get("id")

    def setId(self, id):
        self.set("id", id)

    def getName(self):
        return self.get("name")

    def setName(self, name):
        self.set("name", name)

    def get(self, field):
        return self.attributes.get(field, None)

    def set(self, field, value):
        if isinstance(value, unicode):
            self.attributes[field] = str(value)
        else:
            self.attributes[field] = value

    def setAttributes(self, attributes):
        if attributes:
            self.attributes = attributes

    @classmethod
    def deserialize(cls, entity):
        if "synergy_object" not in entity:
            raise SynergyError("it seems not a Synergy object!")

        synergy_object = entity["synergy_object"]

        if "namespace" not in synergy_object:
            raise SynergyError("synergy_object.namespace not defined!")

        if "name" not in synergy_object:
            raise SynergyError("synergy_object.name not defined!")

        if "version" not in synergy_object:
            raise SynergyError("synergy_object.version mismatch!")

        if synergy_object["version"] != cls.VERSION:
            raise SynergyError("synergy_object.version mis!")

        if synergy_object["namespace"] != "synergy":
            raise SynergyError("unsupported object objtype='%s.%s"
                               % (synergy_object["namespace"],
                                  synergy_object["name"]))

        objInstance = None

        try:
            objName = synergy_object["name"]
            objClass = utils.import_class(objName)
            objInstance = objClass()
        except Exception as ex:
            raise SynergyError("error on deserializing the object %r: %s"
                               % (objName, ex))

        del entity["synergy_object"]

        entity = utils.objectHookHandler(entity)

        for key, value in entity.items():
            if isinstance(value, dict):
                if "synergy_object" in value:
                    objInstance.set(key, SynergyObject.deserialize(value))
                else:
                    objInstance.set(key, value)
            elif isinstance(value, list):
                l = []

                objInstance.set(key, l)

                for item in value:
                    if isinstance(item, dict) and "synergy_object" in item:
                        l.append(SynergyObject.deserialize(item))
                    else:
                        l.append(item)
            else:
                objInstance.set(key, value)

        return objInstance

    def serialize(self):
        name = self.__class__.__module__ + "." + self.__class__.__name__

        result = {"synergy_object": {}}
        result["synergy_object"]["name"] = name
        result["synergy_object"]["version"] = self.VERSION
        result["synergy_object"]["namespace"] = "synergy"

        for key, value in self.attributes.items():
            if isinstance(value, SynergyObject):
                result[key] = value.serialize()
            elif isinstance(value, dict):
                result[key] = {}

                for k, v in value.items():
                    if isinstance(v, SynergyObject):
                        result[key][k] = v.serialize()
                    else:
                        result[key][k] = v
            elif isinstance(value, list):
                result[key] = []

                for item in value:
                    if isinstance(item, SynergyObject):
                        result[key].append(item.serialize())
                    else:
                        result[key].append(item)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value

        return result


class SynergyEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SynergyObject):
            return obj.serialize()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return JSONEncoder.default(self, obj)
