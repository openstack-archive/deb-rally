# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from rally.plugins.openstack.scenarios.ceilometer import meters
from tests.unit import test


class CeilometerMetersTestCase(test.ScenarioTestCase):
    def test_list_meters(self):
        scenario = meters.CeilometerMeters(self.context)
        scenario._list_meters = mock.MagicMock()
        scenario.list_meters()
        scenario._list_meters.assert_called_once_with()
