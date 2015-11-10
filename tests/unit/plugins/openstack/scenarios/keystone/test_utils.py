# Copyright 2013: Mirantis Inc.
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
import six

from rally.plugins.openstack.scenarios.keystone import utils
from tests.unit import fakes
from tests.unit import test

UTILS = "rally.plugins.openstack.scenarios.keystone.utils."


class KeystoneUtilsTestCase(test.TestCase):

    def test_RESOURCE_NAME_PREFIX(self):
        self.assertIsInstance(utils.KeystoneScenario.RESOURCE_NAME_PREFIX,
                              six.string_types)
        # Prefix must be long enough to guarantee that resource
        # to be recognized as created by rally
        self.assertTrue(
            len(utils.KeystoneScenario.RESOURCE_NAME_PREFIX) > 7)

    def test_is_temporary(self):
        prefix = utils.KeystoneScenario.RESOURCE_NAME_PREFIX
        tests = [
            (fakes.FakeResource(name=prefix + "abc"), True),
            (fakes.FakeResource(name="another"), False),
            (fakes.FakeResource(name=prefix[:-3] + "abc"), False)
        ]

        for resource, is_valid in tests:
            self.assertEqual(utils.is_temporary(resource), is_valid)


class KeystoneScenarioTestCase(test.ScenarioTestCase):

    @mock.patch(UTILS + "uuid.uuid4", return_value="pwd")
    @mock.patch("rally.common.utils.generate_random_name",
                return_value="foobarov")
    def test_user_create(self, mock_generate_random_name, mock_uuid4):
        scenario = utils.KeystoneScenario(self.context)
        result = scenario._user_create()

        self.assertEqual(
            self.admin_clients("keystone").users.create.return_value, result)
        self.admin_clients("keystone").users.create.assert_called_once_with(
            "foobarov",
            password=mock_uuid4.return_value,
            email="foobarov@rally.me")
        mock_uuid4.assert_called_with()
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.create_user")

    def test_update_user_enabled(self):
        user = mock.Mock()
        enabled = mock.Mock()
        scenario = utils.KeystoneScenario(self.context)

        scenario._update_user_enabled(user, enabled)
        self.admin_clients(
            "keystone").users.update_enabled.assert_called_once_with(user,
                                                                     enabled)

        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.update_user_enabled")

    @mock.patch("rally.common.utils.generate_random_name")
    def test_role_create(self, mock_generate_random_name):
        scenario = utils.KeystoneScenario(self.context)
        result = scenario._role_create()

        self.assertEqual(
            self.admin_clients("keystone").roles.create.return_value, result)
        self.admin_clients("keystone").roles.create.assert_called_once_with(
            mock_generate_random_name.return_value)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.create_role")

    def test_list_roles_for_user(self):
        user = mock.MagicMock()
        tenant = mock.MagicMock()
        scenario = utils.KeystoneScenario(self.context)

        scenario._list_roles_for_user(user, tenant)

        self.admin_clients(
            "keystone").roles.roles_for_user.assert_called_once_with(user,
                                                                     tenant)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.list_roles")

    def test_role_add(self):
        user = mock.MagicMock()
        role = mock.MagicMock()
        tenant = mock.MagicMock()
        scenario = utils.KeystoneScenario(self.context)

        scenario._role_add(user=user.id, role=role.id, tenant=tenant.id)

        self.admin_clients(
            "keystone").roles.add_user_role.assert_called_once_with(user.id,
                                                                    role.id,
                                                                    tenant.id)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.add_role")

    def test_user_delete(self):
        resource = fakes.FakeResource()
        resource.delete = mock.MagicMock()

        scenario = utils.KeystoneScenario(self.context)
        scenario._resource_delete(resource)
        resource.delete.assert_called_once_with()
        r = "keystone.delete_%s" % resource.__class__.__name__.lower()
        self._test_atomic_action_timer(scenario.atomic_actions(), r)

    def test_role_remove(self):
        user = mock.MagicMock()
        role = mock.MagicMock()
        tenant = mock.MagicMock()
        scenario = utils.KeystoneScenario(self.context)

        scenario._role_remove(user=user, role=role, tenant=tenant)

        self.admin_clients(
            "keystone").roles.remove_user_role.assert_called_once_with(user,
                                                                       role,
                                                                       tenant)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.remove_role")

    @mock.patch("rally.common.utils.generate_random_name")
    def test_tenant_create(self, mock_generate_random_name):
        scenario = utils.KeystoneScenario(self.context)
        result = scenario._tenant_create()

        self.assertEqual(
            self.admin_clients("keystone").tenants.create.return_value, result)
        self.admin_clients("keystone").tenants.create.assert_called_once_with(
            mock_generate_random_name.return_value)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.create_tenant")

    def test_service_create(self):
        service_type = "service_type"
        description = "_description"

        scenario = utils.KeystoneScenario(self.context)
        scenario._generate_random_name = mock.Mock()

        result = scenario._service_create(service_type=service_type,
                                          description=description)

        self.assertEqual(
            self.admin_clients("keystone").services.create.return_value,
            result)
        self.admin_clients("keystone").services.create.assert_called_once_with(
            scenario._generate_random_name.return_value,
            service_type, description)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.create_service")

    @mock.patch("rally.common.utils.generate_random_name",
                return_value="foobarov")
    def test_tenant_create_with_users(self, mock_generate_random_name):
        tenant = mock.MagicMock()
        scenario = utils.KeystoneScenario(self.context)

        scenario._users_create(tenant, users_per_tenant=1, name_length=10)

        self.admin_clients("keystone").users.create.assert_called_once_with(
            "foobarov", password="foobarov", email="foobarov@rally.me",
            tenant_id=tenant.id)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.create_users")

    def test_list_users(self):
        scenario = utils.KeystoneScenario(self.context)
        scenario._list_users()
        self.admin_clients("keystone").users.list.assert_called_once_with()
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.list_users")

    def test_list_tenants(self):
        scenario = utils.KeystoneScenario(self.context)
        scenario._list_tenants()
        self.admin_clients("keystone").tenants.list.assert_called_once_with()
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.list_tenants")

    def test_list_services(self):
        scenario = utils.KeystoneScenario(self.context)
        scenario._list_services()

        self.admin_clients("keystone").services.list.assert_called_once_with()
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.service_list")

    def test_delete_service(self):
        service = mock.MagicMock()
        scenario = utils.KeystoneScenario(self.context)
        scenario._delete_service(service_id=service.id)

        self.admin_clients("keystone").services.delete.assert_called_once_with(
            service.id)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.delete_service")

    def test_get_tenant(self):
        tenant = mock.MagicMock()
        scenario = utils.KeystoneScenario(self.context)
        scenario._get_tenant(tenant_id=tenant.id)

        self.admin_clients("keystone").tenants.get.assert_called_once_with(
            tenant.id)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.get_tenant")

    def test_get_user(self):
        user = mock.MagicMock()
        scenario = utils.KeystoneScenario(self.context)
        scenario._get_user(user_id=user.id)

        self.admin_clients("keystone").users.get.assert_called_once_with(
            user.id)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.get_user")

    def test_get_role(self):
        role = mock.MagicMock()
        scenario = utils.KeystoneScenario(self.context)
        scenario._get_role(role_id=role.id)

        self.admin_clients("keystone").roles.get.assert_called_once_with(
            role.id)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.get_role")

    def test_get_service(self):
        service = mock.MagicMock()
        scenario = utils.KeystoneScenario(self.context)
        scenario._get_service(service_id=service.id)

        self.admin_clients("keystone").services.get.assert_called_once_with(
            service.id)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.get_service")

    def test_update_tenant(self):
        tenant = mock.MagicMock()
        description = tenant.name + "_description_updated_test"
        name = tenant.name + "test_updated_test"
        scenario = utils.KeystoneScenario(self.context)
        scenario._update_tenant(tenant=tenant, name=name,
                                description=description)

        self.admin_clients("keystone").tenants.update.assert_called_once_with(
            tenant.id, name, description)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.update_tenant")

    def test_update_user_password(self):
        password = "pswd"
        user = mock.MagicMock()
        scenario = utils.KeystoneScenario(self.context)

        scenario._update_user_password(password=password, user_id=user.id)

        self.admin_clients(
            "keystone").users.update_password.assert_called_once_with(user.id,
                                                                      password)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.update_user_password")

    @mock.patch("rally.plugins.openstack.scenario.OpenStackScenario."
                "admin_clients")
    def test_update_user_password_v3(self,
                                     mock_open_stack_scenario_admin_clients):
        password = "pswd"
        user = mock.MagicMock()
        scenario = utils.KeystoneScenario()

        type(mock_open_stack_scenario_admin_clients.return_value).version = (
            mock.PropertyMock(return_value="v3"))
        scenario._update_user_password(password=password, user_id=user.id)

        mock_open_stack_scenario_admin_clients(
            "keystone").users.update.assert_called_once_with(
            user.id, password=password)
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.update_user_password")

    def test_get_service_by_name(self):
        scenario = utils.KeystoneScenario(self.context)
        svc_foo, svc_bar = mock.Mock(), mock.Mock()
        scenario._list_services = mock.Mock(return_value=[svc_foo, svc_bar])
        self.assertEqual(scenario._get_service_by_name(svc_bar.name), svc_bar)
        self.assertIsNone(scenario._get_service_by_name("spam"))

    @mock.patch(UTILS + "KeystoneScenario.clients")
    def test_create_ec2credentials(self, mock_clients):
        scenario = utils.KeystoneScenario(self.context)
        creds = mock.Mock()
        mock_clients("keystone").ec2.create.return_value = creds
        create_creds = scenario._create_ec2credentials("user_id",
                                                       "tenant_id")
        self.assertEqual(create_creds, creds)
        mock_clients("keystone").ec2.create.assert_called_once_with(
            "user_id", "tenant_id")
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.create_ec2creds")

    @mock.patch(UTILS + "KeystoneScenario.clients")
    def test_list_ec2credentials(self, mock_clients):
        scenario = utils.KeystoneScenario(self.context)
        creds_list = mock.Mock()
        mock_clients("keystone").ec2.list.return_value = creds_list
        list_creds = scenario._list_ec2credentials("user_id")
        self.assertEqual(list_creds, creds_list)
        mock_clients("keystone").ec2.list.assert_called_once_with("user_id")
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.list_ec2creds")

    @mock.patch(UTILS + "KeystoneScenario.clients")
    def test_delete_ec2credentials(self, mock_clients):
        scenario = utils.KeystoneScenario(self.context)
        mock_clients("keystone").ec2.delete = mock.MagicMock()
        scenario._delete_ec2credential("user_id", "access")
        mock_clients("keystone").ec2.delete.assert_called_once_with("user_id",
                                                                    "access")
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "keystone.delete_ec2creds")
