# Copyright 2014: Rackspace UK
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

import novaclient.exceptions

from rally.common.i18n import _
from rally.common import logging
from rally import osclients
from rally.plugins.openstack.cleanup import manager as resource_manager
from rally.task import context


LOG = logging.getLogger(__name__)


@context.configure(name="keypair", order=310)
class Keypair(context.Context):

    def _generate_keypair(self, credential):
        keypair_name = self.generate_random_name()

        nova_client = osclients.Clients(credential).nova()

        # NOTE(hughsaunders): If keypair exists, it must be deleted as we can't
        # retrieve the private key
        try:
            nova_client.keypairs.delete(keypair_name)
        except novaclient.exceptions.NotFound:
            pass

        keypair = nova_client.keypairs.create(keypair_name)
        return {"private": keypair.private_key,
                "public": keypair.public_key,
                "name": keypair_name,
                "id": keypair.id}

    @logging.log_task_wrapper(LOG.info, _("Enter context: `keypair`"))
    def setup(self):
        for user in self.context["users"]:
            user["keypair"] = self._generate_keypair(user["credential"])

    @logging.log_task_wrapper(LOG.info, _("Exit context: `keypair`"))
    def cleanup(self):
        # TODO(boris-42): Delete only resources created by this context
        resource_manager.cleanup(names=["nova.keypairs"],
                                 users=self.context.get("users", []))
