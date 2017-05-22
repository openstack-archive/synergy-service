import sys
import traceback

from datetime import datetime
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


def import_class(import_str):
    """Returns a class from a string including module and class."""
    mod_str, _sep, class_str = import_str.rpartition('.')
    __import__(mod_str)

    try:
        return getattr(sys.modules[mod_str], class_str)
    except AttributeError:
        raise SynergyError(
            'Class %s cannot be found (%s)' %
            (class_str, traceback.format_exception(*sys.exc_info())))


def instantiate_class(class_str):
    return import_class(class_str)()


def objectHookHandler(json_dict):
    for key, value in json_dict.items():
        if isinstance(value, dict):
            json_dict[key] = objectHookHandler(value)
        else:
            try:
                json_dict[key] = datetime.strptime(value,
                                                   "%Y-%m-%dT%H:%M:%S.%f")
            except Exception as ex:
                pass

    if "synergy_object" in json_dict:
        synergy_object = json_dict["synergy_object"]
        try:
            objClass = import_class(synergy_object["name"])
            objInstance = objClass()
            return objInstance.deserialize(json_dict)
        except SynergyError as ex:
            raise ex
    else:
        return json_dict
