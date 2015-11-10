# Copyright 2014: Mirantis Inc.
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

import jsonschema
import mock

from rally.plugins.openstack.context.cleanup import context
from tests.unit import test


BASE = "rally.plugins.openstack.context.cleanup.context"


class AdminCleanupTestCase(test.TestCase):

    @mock.patch("%s.manager" % BASE)
    def test_validate(self, mock_manager):
        mock_manager.list_resource_names.return_value = set(["a", "b", "c"])
        context.AdminCleanup.validate(["a"])
        mock_manager.list_resource_names.assert_called_once_with(
            admin_required=True)

    @mock.patch("%s.manager" % BASE)
    def test_validate_no_such_cleanup(self, mock_manager):
        mock_manager.list_resource_names.return_value = set(["a", "b", "c"])
        self.assertRaises(context.NoSuchCleanupResources,
                          context.AdminCleanup.validate, ["a", "d"])
        mock_manager.list_resource_names.assert_called_once_with(
            admin_required=True)

    def test_validate_invalid_config(self):
        self.assertRaises(jsonschema.ValidationError,
                          context.AdminCleanup.validate, {})

    @mock.patch("%s.manager.find_resource_managers" % BASE,
                return_value=[mock.MagicMock(), mock.MagicMock()])
    @mock.patch("%s.manager.SeekAndDestroy" % BASE)
    def test_cleanup(self, mock_seek_and_destroy, mock_find_resource_managers):

        ctx = {
            "config": {"admin_cleanup": ["a", "b"]},
            "admin": mock.MagicMock(),
            "users": mock.MagicMock(),
            "task": mock.MagicMock()
        }

        admin_cleanup = context.AdminCleanup(ctx)
        admin_cleanup.setup()
        admin_cleanup.cleanup()

        mock_find_resource_managers.assert_called_once_with(["a", "b"], True)
        mock_seek_and_destroy.assert_has_calls([
            mock.call(
                mock_find_resource_managers.return_value[0],
                ctx["admin"],
                ctx["users"]),
            mock.call().exterminate(),
            mock.call(
                mock_find_resource_managers.return_value[1],
                ctx["admin"],
                ctx["users"]),
            mock.call().exterminate()
        ])


class UserCleanupTestCase(test.TestCase):

    @mock.patch("%s.manager" % BASE)
    def test_validate(self, mock_manager):
        mock_manager.list_resource_names.return_value = set(["a", "b", "c"])
        context.UserCleanup.validate(["a"])
        mock_manager.list_resource_names.assert_called_once_with(
            admin_required=False)

    @mock.patch("%s.manager" % BASE)
    def test_validate_no_such_cleanup(self, mock_manager):
        mock_manager.list_resource_names.return_value = set(["a", "b", "c"])
        self.assertRaises(context.NoSuchCleanupResources,
                          context.UserCleanup.validate, ["a", "b", "d"])
        mock_manager.list_resource_names.assert_called_once_with(
            admin_required=False)

    def test_validate_invalid_config(self):
        self.assertRaises(jsonschema.ValidationError,
                          context.UserCleanup.validate, {})

    @mock.patch("%s.manager.find_resource_managers" % BASE,
                return_value=[mock.MagicMock(), mock.MagicMock()])
    @mock.patch("%s.manager.SeekAndDestroy" % BASE)
    def test_cleanup(self, mock_seek_and_destroy, mock_find_resource_managers):

        ctx = {
            "config": {"cleanup": ["a", "b"]},
            "users": mock.MagicMock(),
            "task": mock.MagicMock()
        }

        admin_cleanup = context.UserCleanup(ctx)
        admin_cleanup.setup()
        admin_cleanup.cleanup()

        mock_find_resource_managers.assert_called_once_with(["a", "b"], False)

        mock_seek_and_destroy.assert_has_calls([
            mock.call(
                mock_find_resource_managers.return_value[0],
                None, ctx["users"]),
            mock.call().exterminate(),
            mock.call(
                mock_find_resource_managers.return_value[1],
                None, ctx["users"]),
            mock.call().exterminate()
        ])
