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

import ddt
import mock

from rally.plugins.openstack.scenarios.neutron import security_groups
from tests.unit import test


@ddt.ddt
class NeutronSecurityGroup(test.TestCase):

    @ddt.data(
        {},
        {"security_group_create_args": {}},
        {"security_group_create_args": {"description": "fake-description"}},
    )
    @ddt.unpack
    def test_create_and_list_security_groups(
            self, security_group_create_args=None):
        neutron_scenario = security_groups.NeutronSecurityGroup()
        security_group_data = security_group_create_args or {}
        neutron_scenario._create_security_group = mock.Mock()
        neutron_scenario._list_security_groups = mock.Mock()
        neutron_scenario.create_and_list_security_groups(
            security_group_create_args=security_group_create_args)
        neutron_scenario._create_security_group.assert_called_once_with(
            **security_group_data)
        neutron_scenario._list_security_groups.assert_called_once_with()

    @ddt.data(
        {},
        {"security_group_create_args": {}},
        {"security_group_create_args": {"description": "fake-description"}},
    )
    @ddt.unpack
    def test_create_and_delete_security_groups(
            self, security_group_create_args=None):
        neutron_scenario = security_groups.NeutronSecurityGroup()
        security_group_data = security_group_create_args or {}
        neutron_scenario._create_security_group = mock.Mock()
        neutron_scenario._delete_security_group = mock.Mock()
        neutron_scenario.create_and_delete_security_groups(
            security_group_create_args=security_group_create_args)
        neutron_scenario._create_security_group.assert_called_once_with(
            **security_group_data)
        neutron_scenario._delete_security_group.assert_called_once_with(
            neutron_scenario._create_security_group.return_value)

    @ddt.data(
        {},
        {"security_group_create_args": {}},
        {"security_group_create_args": {"description": "fake-description"}},
        {"security_group_update_args": {}},
        {"security_group_update_args": {"description": "fake-updated-descr"}},
    )
    @ddt.unpack
    def test_create_and_update_security_groups(
            self, security_group_create_args=None,
            security_group_update_args=None):
        neutron_scenario = security_groups.NeutronSecurityGroup()
        security_group_data = security_group_create_args or {}
        security_group_update_data = security_group_update_args or {}
        neutron_scenario._create_security_group = mock.Mock()
        neutron_scenario._update_security_group = mock.Mock()
        neutron_scenario.create_and_update_security_groups(
            security_group_create_args=security_group_create_args,
            security_group_update_args=security_group_update_args)
        neutron_scenario._create_security_group.assert_called_once_with(
            **security_group_data)
        neutron_scenario._update_security_group.assert_called_once_with(
            neutron_scenario._create_security_group.return_value,
            **security_group_update_data)
