# Copyright 2015: Mirantis Inc.
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

from rally import consts
from rally.plugins.openstack import scenario
from rally.plugins.openstack.scenarios.nova import utils
from rally.task import validation


class NovaNetworks(utils.NovaScenario):
    """Benchmark scenarios for Nova networks."""

    @validation.restricted_parameters("label")
    @validation.required_parameters("start_cidr")
    @validation.required_services(consts.Service.NOVA, consts.Service.NOVA_NET)
    @validation.required_openstack(admin=True)
    @scenario.configure(context={"admin_cleanup": ["nova.networks"]})
    def create_and_list_networks(self, start_cidr, **kwargs):
        """Create nova network and list all networks.

        :param start_cidr: IP range
        :param kwargs: Optional additional arguments for network creation
        """

        self._create_network(start_cidr, **kwargs)
        self._list_networks()

    @validation.restricted_parameters("label")
    @validation.required_parameters("start_cidr")
    @validation.required_services(consts.Service.NOVA, consts.Service.NOVA_NET)
    @validation.required_openstack(admin=True)
    @scenario.configure(context={"admin_cleanup": ["nova.networks"]})
    def create_and_delete_network(self, start_cidr, **kwargs):
        """Create nova network and delete it.

        :param start_cidr: IP range
        :param kwargs: Optional additional arguments for network creation
        """

        net_id = self._create_network(start_cidr, **kwargs)
        self._delete_network(net_id)
