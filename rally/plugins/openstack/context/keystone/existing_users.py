# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from rally.common.i18n import _
from rally.common import log as logging
from rally.common import objects
from rally.common import utils as rutils
from rally import osclients
from rally.plugins.openstack.context.keystone import users
from rally.task import context


LOG = logging.getLogger(__name__)


# NOTE(boris-42): This context should be hidden for now and used only by
#                 benchmark engine.  In future during various refactoring of
#                 validation system and rally CI testing we will make it public

@context.configure(name="existing_users", order=99, hidden=True)
class ExistingUsers(users.UserContextMixin, context.Context):
    """This context supports using existing users in Rally.

       It uses information about deployment to properly
       initialize context["users"] and context["tenants"]

       So there won't be big difference between usage of "users" and
       "existing_users" context.
    """

    # NOTE(boris-42): We don't need to check config schema because
    #                 this is used only by benchmark engine
    CONFIG_SCHEMA = {}

    @rutils.log_task_wrapper(LOG.info, _("Enter context: `existing_users`"))
    def setup(self):
        self.context["users"] = []
        self.context["tenants"] = {}

        for user in self.config:
            user_endpoint = objects.Endpoint(**user)
            user_kclient = osclients.Clients(user_endpoint).keystone()

            if user_kclient.tenant_id not in self.context["tenants"]:
                self.context["tenants"][user_kclient.tenant_id] = {
                    "id": user_kclient.tenant_id,
                    "name": user_kclient.tenant_name
                }

            self.context["users"].append({
                "endpoint": user_endpoint,
                "id": user_kclient.user_id,
                "tenant_id": user_kclient.tenant_id
            })

    @rutils.log_task_wrapper(LOG.info, _("Exit context: `existing_users`"))
    def cleanup(self):
        """These users are not managed by Rally, so don't touch them."""
