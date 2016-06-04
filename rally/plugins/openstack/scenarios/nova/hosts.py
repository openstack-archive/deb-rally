# Copyright 2016 IBM Corp
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

from rally.common import logging
from rally import consts
from rally.plugins.openstack import scenario
from rally.plugins.openstack.scenarios.nova import utils
from rally.task import validation


LOG = logging.getLogger(__name__)


class NovaHosts(utils.NovaScenario):
    """Benchmark scenarios for Nova hosts."""

    @validation.required_services(consts.Service.NOVA)
    @validation.required_openstack(admin=True)
    @scenario.configure()
    def list_hosts(self, zone=None):
        """List all nova hosts.

        Measure the "nova host-list" command performance.

        :param zone: List nova hosts in an availibility-zone.
                     None (default value) means list hosts in all
                     availibility-zones
        """
        self._list_hosts(zone)
