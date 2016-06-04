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

import tempfile

import ddt
from glanceclient import exc as glance_exc
import mock
from oslo_config import cfg

from rally import exceptions
from rally.plugins.openstack.wrappers import glance as glance_wrapper
from tests.unit import test

CONF = cfg.CONF


class GlanceWrapperTestBase(object):
    def test_wrap(self):
        client = mock.MagicMock()
        owner = mock.Mock()
        client.version = "dummy"
        self.assertRaises(exceptions.InvalidArgumentsException,
                          glance_wrapper.wrap, client, owner)


@ddt.ddt
class GlanceV1WrapperTestCase(test.ScenarioTestCase, GlanceWrapperTestBase):
    _tempfile = tempfile.NamedTemporaryFile()

    def setUp(self):
        super(GlanceV1WrapperTestCase, self).setUp()
        self.client = mock.MagicMock()
        self.client.choose_version.return_value = "1"
        self.owner = mock.Mock()
        self.wrapped_client = glance_wrapper.wrap(self.client, self.owner)

    def test_get_image(self):
        image = mock.Mock()

        return_image = self.wrapped_client.get_image(image)

        image.manager.get.assert_called_once_with(image.id)
        self.assertEqual(return_image, image.manager.get.return_value)

    @ddt.data(
        {"location": "image_location"},
        {"location": "image_location", "fakearg": "fake"},
        {"location": "image_location", "name": "image_name"},
        {"location": _tempfile.name})
    @ddt.unpack
    @mock.patch("six.moves.builtins.open")
    def test_create_image(self, mock_open, location, **kwargs):
        return_image = self.wrapped_client.create_image("container_format",
                                                        location,
                                                        "disk_format",
                                                        **kwargs)
        call_args = dict(kwargs)
        call_args["container_format"] = "container_format"
        call_args["disk_format"] = "disk_format"
        if location.startswith("/"):
            call_args["data"] = mock_open.return_value
            mock_open.assert_called_once_with(location)
            mock_open.return_value.close.assert_called_once_with()
        else:
            call_args["copy_from"] = location
        if "name" not in kwargs:
            call_args["name"] = self.owner.generate_random_name.return_value

        self.client().images.create.assert_called_once_with(**call_args)

        self.mock_wait_for_status.mock.assert_called_once_with(
            self.client().images.create.return_value, ["active"],
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.glance_image_create_poll_interval,
            timeout=CONF.benchmark.glance_image_create_timeout)
        self.mock_get_from_manager.mock.assert_called_once_with()
        self.assertEqual(self.mock_wait_for_status.mock.return_value,
                         return_image)

    def test_delete_image(self):
        image = mock.Mock()
        self.wrapped_client.delete_image(image)
        image.delete.assert_called_once_with()
        self.mock_wait_for_status.mock.assert_called_once_with(
            image, ["deleted"],
            check_deletion=True,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.glance_image_delete_poll_interval,
            timeout=CONF.benchmark.glance_image_delete_timeout)
        self.mock_get_from_manager.mock.assert_called_once_with()

    @ddt.data({}, {"fakearg": "fake"})
    def test_list_images(self, filters):
        self.assertEqual(self.wrapped_client.list_images(**filters),
                         self.client().images.list.return_value)
        self.client().images.list.assert_called_once_with(**filters)


@ddt.ddt
class GlanceV2WrapperTestCase(test.ScenarioTestCase, GlanceWrapperTestBase):
    _tempfile = tempfile.NamedTemporaryFile()

    def setUp(self):
        super(GlanceV2WrapperTestCase, self).setUp()
        self.client = mock.MagicMock()
        self.client.choose_version.return_value = "2"
        self.owner = mock.Mock()
        self.wrapped_client = glance_wrapper.wrap(self.client, self.owner)

    def test_get_image(self):
        image = mock.Mock()

        return_image = self.wrapped_client.get_image(image)

        self.client.return_value.images.get.assert_called_once_with(image.id)
        self.assertEqual(return_image,
                         self.client.return_value.images.get.return_value)

    def test__update_image(self):
        image = mock.Mock()

        return_image = self.wrapped_client._update_image(image)

        self.client.return_value.images.get.assert_called_once_with(image.id)
        self.assertEqual(return_image,
                         self.client.return_value.images.get.return_value)

    def test__update_image_not_found(self):
        image = mock.Mock()
        self.client.return_value.images.get.side_effect = (
            glance_exc.HTTPNotFound)

        self.assertRaises(exceptions.GetResourceNotFound,
                          self.wrapped_client._update_image, image)
        self.client.return_value.images.get.assert_called_once_with(image.id)

    @ddt.data(
        {"location": "image_location"},
        {"location": "image_location", "fakearg": "fake"},
        {"location": "image_location", "name": "image_name"},
        {"location": _tempfile.name})
    @ddt.unpack
    @mock.patch("six.moves.builtins.open")
    @mock.patch("requests.get")
    def test_create_image(self, mock_requests_get, mock_open, location,
                          **kwargs):
        self.wrapped_client._update_image = mock.Mock()
        created_image = mock.Mock()
        uploaded_image = mock.Mock()
        self.mock_wait_for_status.mock.side_effect = [created_image,
                                                      uploaded_image]

        return_image = self.wrapped_client.create_image("container_format",
                                                        location,
                                                        "disk_format",
                                                        **kwargs)
        create_args = dict(kwargs)
        create_args["container_format"] = "container_format"
        create_args["disk_format"] = "disk_format"
        if "name" not in kwargs:
            create_args["name"] = self.owner.generate_random_name.return_value

        self.client().images.create.assert_called_once_with(**create_args)

        if location.startswith("/"):
            data = mock_open.return_value
            mock_open.assert_called_once_with(location)
        else:
            data = mock_requests_get.return_value.raw
            mock_requests_get.assert_called_once_with(location)
        data.close.assert_called_once_with()
        self.client().images.upload.assert_called_once_with(created_image.id,
                                                            data)

        self.mock_wait_for_status.mock.assert_has_calls([
            mock.call(
                self.client().images.create.return_value, ["queued"],
                update_resource=self.wrapped_client._update_image,
                check_interval=CONF.benchmark.
                glance_image_create_poll_interval,
                timeout=CONF.benchmark.glance_image_create_timeout),
            mock.call(
                created_image, ["active"],
                update_resource=self.wrapped_client._update_image,
                check_interval=CONF.benchmark.
                glance_image_create_poll_interval,
                timeout=mock.ANY)])
        self.assertEqual(uploaded_image, return_image)

    def test_delete_image(self):
        image = mock.Mock()
        self.wrapped_client.delete_image(image)
        self.client.return_value.images.delete.assert_called_once_with(
            image.id)
        self.mock_wait_for_status.mock.assert_called_once_with(
            image, ["deleted"],
            check_deletion=True,
            update_resource=self.wrapped_client._update_image,
            check_interval=CONF.benchmark.glance_image_delete_poll_interval,
            timeout=CONF.benchmark.glance_image_delete_timeout)

    @ddt.data({}, {"fakearg": "fake"})
    def test_list_images(self, filters):
        self.assertEqual(self.wrapped_client.list_images(**filters),
                         self.client().images.list.return_value)
        self.client().images.list.assert_called_once_with(filters=filters)
