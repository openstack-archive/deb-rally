# Copyright 2013 Cisco Systems Inc.
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

from rally.plugins.openstack.scenarios.nova import hypervisors
from tests.unit import test


NOVA_HYPERVISORS_MODULE = "rally.plugins.openstack.scenarios.nova.hypervisors"
NOVA_HYPERVISORS = NOVA_HYPERVISORS_MODULE + ".NovaHypervisors"


class NovaHypervisorsTestCase(test.ScenarioTestCase):
    def test_list_hypervisors(self):
        scenario = hypervisors.NovaHypervisors(self.context)
        scenario._list_hypervisors = mock.Mock()
        scenario.list_hypervisors(detailed=False)
        scenario._list_hypervisors.assert_called_once_with(False)
