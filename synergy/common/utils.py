import base64
import binascii
import ConfigParser
import io
import sys
import traceback

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
        raise ImportError(
            'Class %s cannot be found (%s)' %
            (class_str, traceback.format_exception(*sys.exc_info())))


def objectHookHandler(parsed_dict):
    if "synergy_object" in parsed_dict:
        synergy_object = parsed_dict["synergy_object"]
        try:
            objClass = import_class(synergy_object["name"])
            objInstance = objClass()
            return objInstance.deserialize(parsed_dict)
        except Exception as ex:
            raise ex
    else:
        return parsed_dict


def encodeBase64(s):
    try:
        return base64.encodestring(s)
    except binascii.Error:
        raise binascii.Error


def decodeBase64(s):
    try:
        return base64.decodestring(s)
    except binascii.Error:
        raise binascii.Error


def getConfigParameter(data, key, section="DEFAULT"):
    config = ConfigParser.RawConfigParser(allow_no_value=True)
    config.readfp(io.BytesIO(data))
    return config.get(section, key)
