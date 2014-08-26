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

""" Test for orchestrator. """

import collections

import mock

from rally.benchmark.scenarios import base
from rally import consts
from rally.orchestrator import api
from tests import fakes
from tests import test

FAKE_DEPLOY_CONFIG = {
    # TODO(akscram): A fake engine is more suitable for that.
    "type": "ExistingCloud",
    "auth_url": "http://example.net:5000/v2.0/",
    "admin": {
        "username": "admin",
        "password": "myadminpass",
        "tenant_name": "demo",
        "domain_name": None,
        "project_domain_name": "Default",
        "user_domain_name": "Default"
    },
    "region_name": "RegionOne",
    "use_public_urls": False,
    "admin_port": 35357
}


FAKE_TASK_CONFIG = {
    "FakeScenario.fake": [
        {
            "args": {},
            "runner": {
                "type": "constant",
                "timeout": 10000,
                "times": 3,
                "concurrency": 2,
            },
            "context": {
                "users": {
                    "tenants": 5,
                    "users_per_tenant": 6,
                }
            }
        }
    ]
}


class FakeScenario(base.Scenario):
    @classmethod
    def fake(cls, context):
        pass


# TODO(akscram): The test cases are very superficial because they test
#                only datascenario_base.operations and actually no more. Each
#                case in this test should to mock everything external.
class APITestCase(test.TestCase):

    def setUp(self):
        super(APITestCase, self).setUp()
        self.deploy_config = FAKE_DEPLOY_CONFIG
        self.task_config = FAKE_TASK_CONFIG
        self.deploy_uuid = "599bdf1d-fe77-461a-a810-d59b1490f4e3"
        admin_endpoint = FAKE_DEPLOY_CONFIG.copy()
        admin_endpoint.pop("type")
        admin_endpoint.update(admin_endpoint.pop("admin"))
        admin_endpoint["permission"] = consts.EndpointPermission.ADMIN
        self.endpoints = {"admin": admin_endpoint, "users": []}

        self.task_uuid = "b0d9cd6c-2c94-4417-a238-35c7019d0257"
        self.task = {
            "uuid": self.task_uuid,
        }
        self.deployment = {
            "uuid": self.deploy_uuid,
            "name": "fake_name",
            "config": self.deploy_config,
            "admin": self.endpoints["admin"],
            "users": []
        }
        self.tempest = mock.Mock()

    @mock.patch("rally.objects.Task")
    def test_create_task(self, mock_task):
        deployment_uuid = "b0d9cd6c-2c94-4417-a238-35c7019d0257"
        tag = "a"
        api.create_task(deployment_uuid, tag)
        mock_task.assert_called_once_with(deployment_uuid=deployment_uuid,
                                          tag=tag)

    @mock.patch("rally.benchmark.engine.BenchmarkEngine"
                "._validate_config_semantic")
    @mock.patch("rally.benchmark.engine.BenchmarkEngine"
                "._validate_config_syntax")
    @mock.patch("rally.benchmark.engine.BenchmarkEngine"
                "._validate_config_scenarios_name")
    @mock.patch("rally.benchmark.engine.osclients")
    @mock.patch("rally.benchmark.engine.base_runner.ScenarioRunner.get_runner")
    @mock.patch("rally.objects.deploy.db.deployment_get")
    @mock.patch("rally.objects.task.db.task_result_create")
    @mock.patch("rally.objects.task.db.task_update")
    @mock.patch("rally.objects.task.db.task_create")
    def test_start_task(self, mock_task_create, mock_task_update,
                        mock_task_result_create, mock_deploy_get,
                        mock_utils_runner, mock_osclients,
                        mock_validate_names, mock_validate_syntax,
                        mock_validate_semantic):
        mock_task_create.return_value = self.task
        mock_task_update.return_value = self.task
        mock_deploy_get.return_value = self.deployment

        mock_utils_runner.return_value = mock_runner = mock.Mock()
        mock_runner.result_queue = collections.deque(["fake_result"])

        mock_runner.run.return_value = 42
        mock_osclients.Clients.return_value = fakes.FakeClients()

        api.start_task(self.deploy_uuid, self.task_config)

        mock_deploy_get.assert_called_once_with(self.deploy_uuid)
        mock_task_create.assert_called_once_with({
            "deployment_uuid": self.deploy_uuid,
        })
        mock_task_update.assert_has_calls([
            mock.call(self.task_uuid, {"status": consts.TaskStatus.VERIFYING}),
            mock.call(self.task_uuid, {"status": consts.TaskStatus.RUNNING}),
            mock.call(self.task_uuid, {"status": consts.TaskStatus.FINISHED})
        ])
        # NOTE(akscram): It looks really awful, but checks degradation.
        mock_task_result_create.assert_called_once_with(
            self.task_uuid,
            {
                "kw": {
                    "args": {},
                    "runner": {
                        "type": "constant",
                        "timeout": 10000,
                        "times": 3,
                        "concurrency": 2,
                    },
                    "context": {
                        "users": {
                            "tenants": 5,
                            "users_per_tenant": 6,
                        }
                    }
                },
                "name": "FakeScenario.fake",
                "pos": 0,
            },
            {
                "raw": ["fake_result"],
                "scenario_duration": 42
            }
        )

    def test_abort_task(self):
        self.assertRaises(NotImplementedError, api.abort_task,
                          self.task_uuid)

    @mock.patch("rally.objects.task.db.task_delete")
    def test_delete_task(self, mock_delete):
        api.delete_task(self.task_uuid)
        mock_delete.assert_called_once_with(
            self.task_uuid,
            status=consts.TaskStatus.FINISHED)

    @mock.patch("rally.objects.task.db.task_delete")
    def test_delete_task_force(self, mock_delete):
        api.delete_task(self.task_uuid, force=True)
        mock_delete.assert_called_once_with(self.task_uuid, status=None)

    @mock.patch("rally.objects.deploy.db.deployment_update")
    @mock.patch("rally.objects.deploy.db.deployment_create")
    def test_create_deploy(self, mock_create, mock_update):
        mock_create.return_value = self.deployment
        mock_update.return_value = self.deployment
        api.create_deploy(self.deploy_config, "fake_deploy")
        mock_create.assert_called_once_with({
            "name": "fake_deploy",
            "config": self.deploy_config,
        })
        mock_update.assert_has_calls([
            mock.call(self.deploy_uuid, self.endpoints)
        ])

    @mock.patch("rally.objects.deploy.db.deployment_delete")
    @mock.patch("rally.objects.deploy.db.deployment_update")
    @mock.patch("rally.objects.deploy.db.deployment_get")
    def test_destroy_deploy(self, mock_get, mock_update, mock_delete):
        mock_get.return_value = self.deployment
        mock_update.return_value = self.deployment
        api.destroy_deploy(self.deploy_uuid)
        mock_get.assert_called_once_with(self.deploy_uuid)
        mock_delete.assert_called_once_with(self.deploy_uuid)

    @mock.patch("rally.objects.deploy.db.deployment_update")
    @mock.patch("rally.objects.deploy.db.deployment_get")
    def test_recreate_deploy(self, mock_get, mock_update):
        mock_get.return_value = self.deployment
        mock_update.return_value = self.deployment
        api.recreate_deploy(self.deploy_uuid)
        mock_get.assert_called_once_with(self.deploy_uuid)
        mock_update.assert_has_calls([
            mock.call(self.deploy_uuid, self.endpoints)
        ])

    @mock.patch("rally.orchestrator.api.objects.Verification")
    @mock.patch("rally.verification.verifiers.tempest.tempest.Tempest")
    def test_verify(self, mock_tempest, mock_verification):
        mock_tempest.return_value = self.tempest
        self.tempest.is_installed.return_value = True
        api.verify(self.deploy_uuid, "smoke", None)

        self.tempest.is_installed.assert_called_once_with()
        self.tempest.verify.assert_called_once_with(set_name="smoke",
                                                    regex=None)

    @mock.patch("rally.orchestrator.api.objects.Verification")
    @mock.patch("rally.verification.verifiers.tempest.tempest.Tempest")
    def test_verify_tempest_not_installed(self, mock_tempest,
                                          mock_verification):
        mock_tempest.return_value = self.tempest
        self.tempest.is_installed.return_value = False
        api.verify(self.deploy_uuid, "smoke", None)

        self.tempest.is_installed.assert_called_once_with()
        self.tempest.install.assert_called_once_with()
        self.tempest.verify.assert_called_once_with(set_name="smoke",
                                                    regex=None)
