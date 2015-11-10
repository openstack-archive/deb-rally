# Copyright 2014: Intel Inc.
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
from rally.plugins.openstack.scenarios.neutron import utils
from rally.task import validation


class NeutronNetworks(utils.NeutronScenario):
    """Benchmark scenarios for Neutron."""

    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_list_networks(self, network_create_args=None):
        """Create a network and then list all networks.

        Measure the "neutron net-list" command performance.

        If you have only 1 user in your context, you will
        add 1 network on every iteration. So you will have more
        and more networks and will be able to measure the
        performance of the "neutron net-list" command depending on
        the number of networks owned by users.

        :param network_create_args: dict, POST /v2.0/networks request options
        """
        self._create_network(network_create_args or {})
        self._list_networks()

    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_update_networks(self,
                                   network_update_args,
                                   network_create_args=None):
        """Create and update a network.

        Measure the "neutron net-create and net-update" command performance.

        :param network_update_args: dict, PUT /v2.0/networks update request
        :param network_create_args: dict, POST /v2.0/networks request options
        """
        network = self._create_network(network_create_args or {})
        self._update_network(network, network_update_args)

    @validation.required_services(consts.Service.NEUTRON)
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_delete_networks(self, network_create_args=None):
        """Create and delete a network.

        Measure the "neutron net-create" and "net-delete" command performance.

        :param network_create_args: dict, POST /v2.0/networks request options
        """
        network = self._create_network(network_create_args or {})
        self._delete_network(network["network"])

    @validation.number("subnets_per_network", minval=1, integer_only=True)
    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_list_subnets(self,
                                network_create_args=None,
                                subnet_create_args=None,
                                subnet_cidr_start=None,
                                subnets_per_network=None):
        """Create and a given number of subnets and list all subnets.

        The scenario creates a network, a given number of subnets and then
        lists subnets.

        :param network_create_args: dict, POST /v2.0/networks request options
        :param subnet_create_args: dict, POST /v2.0/subnets request options
        :param subnet_cidr_start: str, start value for subnets CIDR
        :param subnets_per_network: int, number of subnets for one network
        """
        self._create_network_and_subnets(network_create_args or {},
                                         subnet_create_args or {},
                                         subnets_per_network,
                                         subnet_cidr_start)
        self._list_subnets()

    @validation.number("subnets_per_network", minval=1, integer_only=True)
    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_update_subnets(self,
                                  subnet_update_args,
                                  network_create_args=None,
                                  subnet_create_args=None,
                                  subnet_cidr_start=None,
                                  subnets_per_network=None):
        """Create and update a subnet.

        The scenario creates a network, a given number of subnets
        and then updates the subnet. This scenario measures the
        "neutron subnet-update" command performance.

        :param subnet_update_args: dict, PUT /v2.0/subnets update options
        :param network_create_args: dict, POST /v2.0/networks request options
        :param subnet_create_args: dict, POST /v2.0/subnets request options
        :param subnet_cidr_start: str, start value for subnets CIDR
        :param subnets_per_network: int, number of subnets for one network
        """
        network, subnets = self._create_network_and_subnets(
            network_create_args or {},
            subnet_create_args or {},
            subnets_per_network,
            subnet_cidr_start)

        for subnet in subnets:
            self._update_subnet(subnet, subnet_update_args)

    @validation.required_parameters("subnets_per_network")
    @validation.required_services(consts.Service.NEUTRON)
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_delete_subnets(self,
                                  network_create_args=None,
                                  subnet_create_args=None,
                                  subnet_cidr_start=None,
                                  subnets_per_network=None):
        """Create and delete a given number of subnets.

        The scenario creates a network, a given number of subnets and then
        deletes subnets.

        :param network_create_args: dict, POST /v2.0/networks request options
        :param subnet_create_args: dict, POST /v2.0/subnets request options
        :param subnet_cidr_start: str, start value for subnets CIDR
        :param subnets_per_network: int, number of subnets for one network
        """
        network, subnets = self._create_network_and_subnets(
            network_create_args or {},
            subnet_create_args or {},
            subnets_per_network,
            subnet_cidr_start)

        for subnet in subnets:
            self._delete_subnet(subnet)

    @validation.number("subnets_per_network", minval=1, integer_only=True)
    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_list_routers(self,
                                network_create_args=None,
                                subnet_create_args=None,
                                subnet_cidr_start=None,
                                subnets_per_network=None,
                                router_create_args=None):
        """Create and a given number of routers and list all routers.

        Create a network, a given number of subnets and routers
        and then list all routers.

        :param network_create_args: dict, POST /v2.0/networks request options
        :param subnet_create_args: dict, POST /v2.0/subnets request options
        :param subnet_cidr_start: str, start value for subnets CIDR
        :param subnets_per_network: int, number of subnets for one network
        :param router_create_args: dict, POST /v2.0/routers request options
        """
        network, subnets = self._create_network_and_subnets(
            network_create_args or {},
            subnet_create_args or {},
            subnets_per_network,
            subnet_cidr_start)

        for subnet in subnets:
            router = self._create_router(router_create_args or {})
            self.clients("neutron").add_interface_router(
                router["router"]["id"],
                {"subnet_id": subnet["subnet"]["id"]})

        self._list_routers()

    @validation.number("subnets_per_network", minval=1, integer_only=True)
    @validation.required_parameters("subnets_per_network")
    @validation.required_services(consts.Service.NEUTRON)
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_update_routers(self,
                                  router_update_args,
                                  network_create_args=None,
                                  subnet_create_args=None,
                                  subnet_cidr_start=None,
                                  subnets_per_network=None,
                                  router_create_args=None):
        """Create and update a given number of routers.

        Create a network, a given number of subnets and routers
        and then updating all routers.

        :param router_update_args: dict, PUT /v2.0/routers update options
        :param network_create_args: dict, POST /v2.0/networks request options
        :param subnet_create_args: dict, POST /v2.0/subnets request options
        :param subnet_cidr_start: str, start value for subnets CIDR
        :param subnets_per_network: int, number of subnets for one network
        :param router_create_args: dict, POST /v2.0/routers request options
        """
        network, subnets = self._create_network_and_subnets(
            network_create_args or {},
            subnet_create_args or {},
            subnets_per_network,
            subnet_cidr_start)

        for subnet in subnets:
            router = self._create_router(router_create_args or {})
            self.clients("neutron").add_interface_router(
                router["router"]["id"],
                {"subnet_id": subnet["subnet"]["id"]})
            self._update_router(router, router_update_args)

    @validation.required_parameters("subnets_per_network")
    @validation.required_services(consts.Service.NEUTRON)
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_delete_routers(self,
                                  network_create_args=None,
                                  subnet_create_args=None,
                                  subnet_cidr_start=None,
                                  subnets_per_network=None,
                                  router_create_args=None):
        """Create and delete a given number of routers.

        Create a network, a given number of subnets and routers
        and then delete all routers.

        :param network_create_args: dict, POST /v2.0/networks request options
        :param subnet_create_args: dict, POST /v2.0/subnets request options
        :param subnet_cidr_start: str, start value for subnets CIDR
        :param subnets_per_network: int, number of subnets for one network
        :param router_create_args: dict, POST /v2.0/routers request options
        """
        network, subnets = self._create_network_and_subnets(
            network_create_args or {},
            subnet_create_args or {},
            subnets_per_network,
            subnet_cidr_start)

        routers = []
        for subnet in subnets:
            router = self._create_router(router_create_args or {})
            self.clients("neutron").add_interface_router(
                router["router"]["id"],
                {"subnet_id": subnet["subnet"]["id"]})
            routers.append(router)

        for e in range(subnets_per_network):
            router = routers[e]
            subnet = subnets[e]
            self.clients("neutron").remove_interface_router(
                router["router"]["id"],
                {"subnet_id": subnet["subnet"]["id"]})
            self._delete_router(router)

    @validation.number("ports_per_network", minval=1, integer_only=True)
    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_list_ports(self,
                              network_create_args=None,
                              port_create_args=None,
                              ports_per_network=None):
        """Create and a given number of ports and list all ports.

        :param network_create_args: dict, POST /v2.0/networks request options
        :param port_create_args: dict, POST /v2.0/ports request options
        :param ports_per_network: int, number of ports for one network
        """
        network = self._create_network(network_create_args or {})
        for i in range(ports_per_network):
            self._create_port(network, port_create_args or {})

        self._list_ports()

    @validation.number("ports_per_network", minval=1, integer_only=True)
    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_update_ports(self,
                                port_update_args,
                                network_create_args=None,
                                port_create_args=None,
                                ports_per_network=None):
        """Create and update a given number of ports.

        Measure the "neutron port-create" and "neutron port-update" commands
        performance.

        :param port_update_args: dict, PUT /v2.0/ports update request options
        :param network_create_args: dict, POST /v2.0/networks request options
        :param port_create_args: dict, POST /v2.0/ports request options
        :param ports_per_network: int, number of ports for one network
        """
        network = self._create_network(network_create_args or {})
        for i in range(ports_per_network):
            port = self._create_port(network, port_create_args or {})
            self._update_port(port, port_update_args)

    @validation.required_parameters("ports_per_network")
    @validation.required_services(consts.Service.NEUTRON)
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_delete_ports(self,
                                network_create_args=None,
                                port_create_args=None,
                                ports_per_network=None):
        """Create and delete a port.

        Measure the "neutron port-create" and "neutron port-delete" commands
        performance.

        :param network_create_args: dict, POST /v2.0/networks request options
        :param port_create_args: dict, POST /v2.0/ports request options
        :param ports_per_network: int, number of ports for one network
        """
        network = self._create_network(network_create_args or {})
        for i in range(ports_per_network):
            port = self._create_port(network, port_create_args or {})
            self._delete_port(port)

    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @validation.external_network_exists("floating_network")
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_list_floating_ips(self, floating_network=None,
                                     floating_ip_args=None):
        """Create and list floating IPs.

        Measure the "neutron floating-ip-create" and "neutron floating-ip-list"
        commands performance.

        :param floating_network: str, external network for floating IP creation
        :param floating_ip_args: dict, POST /floatingips request options
        """
        floating_ip_args = floating_ip_args or {}
        self._create_floatingip(floating_network, **floating_ip_args)
        self._list_floating_ips()

    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @validation.external_network_exists("floating_network")
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_delete_floating_ips(self, floating_network=None,
                                       floating_ip_args=None):
        """Create and delete floating IPs.

        Measure the "neutron floating-ip-create" and "neutron
        floating-ip-delete" commands performance.

        :param floating_network: str, external network for floating IP creation
        :param floating_ip_args: dict, POST /floatingips request options
        """
        floating_ip_args = floating_ip_args or {}
        floating_ip = self._create_floatingip(floating_network,
                                              **floating_ip_args)
        self._delete_floating_ip(floating_ip["floatingip"])
