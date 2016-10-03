# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from synergy.common.serializer import SynergyEncoder
from synergy.common.serializer import SynergyObject
from synergy.tests import base


class TestSerializer(base.TestCase):

    def setUp(self):
        super(TestSerializer, self).setUp()
        self.ser = SynergyObject()

    def test_set_get_Id(self):
        self.ser.setId('test_id')
        self.assertEqual('test_id', self.ser.getId())

    def test_set_get_Name(self):
        self.ser.setName('test_name')
        self.assertEqual('test_name', self.ser.getName())

    def test_set_get(self):
        self.ser.set('value', 'test_value')
        self.assertEqual('test_value', self.ser.get('value'))

    def test_Serialize(self):
        result = self.ser.serialize()
        self.assertEqual('1.0', result["synergy_object"]["version"])
        self.assertEqual("synergy", result["synergy_object"]["namespace"])

    def test_Deserialize(self):
        synObj = SynergyObject()
        synObj.setName('test_name')
        synObjSer = synObj.serialize()
        objInst = SynergyObject.deserialize(synObjSer)
        self.assertEqual('test_name', objInst.getName())


class TestSynergyEncoder(base.TestCase):

    def setUp(self):
        super(TestSynergyEncoder, self).setUp()
        self.se = SynergyEncoder()

    def test_SynergyEncoder(self):
        synObj = SynergyObject()
        synObjEnc = self.se.default(synObj)
        self.assertEqual('1.0', synObjEnc["synergy_object"]["version"])
