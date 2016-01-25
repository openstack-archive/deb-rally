# Copyright 2014 Red Hat, Inc. <http://www.redhat.com>
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
from rally.task import atomic
from rally.task import validation


class Authenticate(scenario.OpenStackScenario):
    """Benchmark scenarios for the authentication mechanism.

    Benchmark scenarios for different types of OpenStack clients like Keystone,
    Nova etc.
    """

    @validation.required_openstack(users=True)
    @scenario.configure()
    def keystone(self):
        """Check Keystone Client."""
        self.clients("keystone")

    @validation.number("repetitions", minval=1)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def validate_glance(self, repetitions):
        """Check Glance Client to ensure validation of token.

        Creation of the client does not ensure validation of the token.
        We have to do some minimal operation to make sure token gets validated.
        In following we are checking for non-existent image.

        :param repetitions: number of times to validate
        """
        glance_client = self.clients("glance")
        image_name = "__intentionally_non_existent_image___"
        for i in range(repetitions):
            with atomic.ActionTimer(self, "authenticate.validate_glance"):
                list(glance_client.images.list(name=image_name))

    @validation.number("repetitions", minval=1)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def validate_nova(self, repetitions):
        """Check Nova Client to ensure validation of token.

        Creation of the client does not ensure validation of the token.
        We have to do some minimal operation to make sure token gets validated.

        :param repetitions: number of times to validate
        """
        nova_client = self.clients("nova")
        for i in range(repetitions):
            with atomic.ActionTimer(self, "authenticate.validate_nova"):
                nova_client.flavors.list()

    @validation.number("repetitions", minval=1)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def validate_cinder(self, repetitions):
        """Check Cinder Client to ensure validation of token.

        Creation of the client does not ensure validation of the token.
        We have to do some minimal operation to make sure token gets validated.

        :param repetitions: number of times to validate
        """
        cinder_client = self.clients("cinder")
        for i in range(repetitions):
            with atomic.ActionTimer(self, "authenticate.validate_cinder"):
                cinder_client.volume_types.list()

    @validation.number("repetitions", minval=1)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def validate_neutron(self, repetitions):
        """Check Neutron Client to ensure validation of token.

        Creation of the client does not ensure validation of the token.
        We have to do some minimal operation to make sure token gets validated.

        :param repetitions: number of times to validate
        """
        neutron_client = self.clients("neutron")
        for i in range(repetitions):
            with atomic.ActionTimer(self, "authenticate.validate_neutron"):
                neutron_client.list_networks()

    @validation.number("repetitions", minval=1)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def validate_heat(self, repetitions):
        """Check Heat Client to ensure validation of token.

        Creation of the client does not ensure validation of the token.
        We have to do some minimal operation to make sure token gets validated.

        :param repetitions: number of times to validate
        """
        heat_client = self.clients("heat")
        for i in range(repetitions):
            with atomic.ActionTimer(self, "authenticate.validate_heat"):
                list(heat_client.stacks.list(limit=0))

    @validation.number("repetitions", minval=1)
    @validation.required_openstack(users=True)
    @validation.required_services(consts.Service.MONASCA)
    @scenario.configure()
    def validate_monasca(self, repetitions):
        """Check Monasca Client to ensure validation of token.

        Creation of the client does not ensure validation of the token.
        We have to do some minimal operation to make sure token gets validated.

        :param repetitions: number of times to validate
        """
        monasca_client = self.clients("monasca")
        for i in range(repetitions):
            with atomic.ActionTimer(self, "authenticate.validate_monasca"):
                list(monasca_client.metrics.list(limit=0))
