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

import ddt
import mock

from rally import exceptions as rally_exceptions
from rally.plugins.openstack.scenarios.nova import servers
from tests.unit import fakes
from tests.unit import test


NOVA_SERVERS_MODULE = "rally.plugins.openstack.scenarios.nova.servers"
NOVA_SERVERS = NOVA_SERVERS_MODULE + ".NovaServers"


@ddt.ddt
class NovaServersTestCase(test.ScenarioTestCase):

    def test_boot_rescue_unrescue(self):
        actions = [{"rescue_unrescue": 5}]
        fake_server = mock.MagicMock()
        scenario = servers.NovaServers(self.context)
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._rescue_server = mock.MagicMock()
        scenario._unrescue_server = mock.MagicMock()
        scenario._delete_server = mock.MagicMock()

        scenario.boot_and_bounce_server("img", 1, actions=actions)
        scenario._boot_server.assert_called_once_with("img", 1)
        server_calls = []
        for i in range(5):
            server_calls.append(mock.call(fake_server))
        self.assertEqual(5, scenario._rescue_server.call_count,
                         "Rescue not called 5 times")
        self.assertEqual(5, scenario._unrescue_server.call_count,
                         "Unrescue not called 5 times")
        scenario._rescue_server.assert_has_calls(server_calls)
        scenario._unrescue_server.assert_has_calls(server_calls)
        scenario._delete_server.assert_called_once_with(fake_server,
                                                        force=False)

    def test_boot_stop_start(self):
        actions = [{"stop_start": 5}]
        fake_server = mock.MagicMock()
        scenario = servers.NovaServers(self.context)
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._start_server = mock.MagicMock()
        scenario._stop_server = mock.MagicMock()
        scenario._delete_server = mock.MagicMock()

        scenario.boot_and_bounce_server("img", 1, actions=actions)

        scenario._boot_server.assert_called_once_with("img", 1)
        server_calls = []
        for i in range(5):
            server_calls.append(mock.call(fake_server))
        self.assertEqual(5, scenario._stop_server.call_count,
                         "Stop not called 5 times")
        self.assertEqual(5, scenario._start_server.call_count,
                         "Start not called 5 times")
        scenario._stop_server.assert_has_calls(server_calls)
        scenario._start_server.assert_has_calls(server_calls)
        scenario._delete_server.assert_called_once_with(fake_server,
                                                        force=False)

    def test_multiple_bounce_actions(self):
        actions = [{"hard_reboot": 5}, {"stop_start": 8}]
        fake_server = mock.MagicMock()
        scenario = servers.NovaServers(self.context)

        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario._delete_server = mock.MagicMock()
        scenario._reboot_server = mock.MagicMock()
        scenario._stop_and_start_server = mock.MagicMock()
        scenario.generate_random_name = mock.MagicMock(return_value="name")

        scenario.boot_and_bounce_server("img", 1, actions=actions)
        scenario._boot_server.assert_called_once_with("img", 1)
        server_calls = []
        for i in range(5):
            server_calls.append(mock.call(fake_server))
        self.assertEqual(5, scenario._reboot_server.call_count,
                         "Reboot not called 5 times")
        scenario._reboot_server.assert_has_calls(server_calls)
        server_calls = []
        for i in range(8):
            server_calls.append(mock.call(fake_server))
        self.assertEqual(8, scenario._stop_and_start_server.call_count,
                         "Stop/Start not called 8 times")
        scenario._stop_and_start_server.assert_has_calls(server_calls)
        scenario._delete_server.assert_called_once_with(fake_server,
                                                        force=False)

    def test_boot_lock_unlock_and_delete(self):
        server = fakes.FakeServer()
        image = fakes.FakeImage()
        flavor = fakes.FakeFlavor()

        scenario = servers.NovaServers(self.context)
        scenario._boot_server = mock.Mock(return_value=server)
        scenario._lock_server = mock.Mock(side_effect=lambda s: s.lock())
        scenario._unlock_server = mock.Mock(side_effect=lambda s: s.unlock())
        scenario._delete_server = mock.Mock(
            side_effect=lambda s, **kwargs:
                self.assertFalse(getattr(s, "OS-EXT-STS:locked", False)))

        scenario.boot_lock_unlock_and_delete(image, flavor, fakearg="fakearg")

        scenario._boot_server.assert_called_once_with(image, flavor,
                                                      fakearg="fakearg")
        scenario._lock_server.assert_called_once_with(server)
        scenario._unlock_server.assert_called_once_with(server)
        scenario._delete_server.assert_called_once_with(server, force=False)

    def test_validate_actions(self):
        actions = [{"hardd_reboot": 6}]
        scenario = servers.NovaServers(self.context)

        self.assertRaises(rally_exceptions.InvalidConfigException,
                          scenario.boot_and_bounce_server,
                          1, 1, actions=actions)
        actions = [{"hard_reboot": "no"}]
        self.assertRaises(rally_exceptions.InvalidConfigException,
                          scenario.boot_and_bounce_server,
                          1, 1, actions=actions)
        actions = {"hard_reboot": 6}
        self.assertRaises(rally_exceptions.InvalidConfigException,
                          scenario.boot_and_bounce_server,
                          1, 1, actions=actions)
        actions = {"hard_reboot": -1}
        self.assertRaises(rally_exceptions.InvalidConfigException,
                          scenario.boot_and_bounce_server,
                          1, 1, actions=actions)
        actions = {"hard_reboot": 0}
        self.assertRaises(rally_exceptions.InvalidConfigException,
                          scenario.boot_and_bounce_server,
                          1, 1, actions=actions)

    def _verify_reboot(self, soft=True):
        actions = [{"soft_reboot" if soft else "hard_reboot": 5}]
        fake_server = mock.MagicMock()
        scenario = servers.NovaServers(self.context)

        scenario._reboot_server = mock.MagicMock()
        scenario._soft_reboot_server = mock.MagicMock()
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario._delete_server = mock.MagicMock()
        scenario.generate_random_name = mock.MagicMock(return_value="name")

        scenario.boot_and_bounce_server("img", 1, actions=actions)

        scenario._boot_server.assert_called_once_with("img", 1)
        server_calls = []
        for i in range(5):
            server_calls.append(mock.call(fake_server))
        if soft:
            self.assertEqual(5, scenario._soft_reboot_server.call_count,
                             "Reboot not called 5 times")
            scenario._soft_reboot_server.assert_has_calls(server_calls)
        else:
            self.assertEqual(5, scenario._reboot_server.call_count,
                             "Reboot not called 5 times")
            scenario._reboot_server.assert_has_calls(server_calls)
        scenario._delete_server.assert_called_once_with(fake_server,
                                                        force=False)

    def test_boot_soft_reboot(self):
        self._verify_reboot(soft=True)

    def test_boot_hard_reboot(self):
        self._verify_reboot(soft=False)

    def test_boot_and_delete_server(self):
        fake_server = object()

        scenario = servers.NovaServers(self.context)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario._delete_server = mock.MagicMock()
        scenario.sleep_between = mock.MagicMock()

        scenario.boot_and_delete_server("img", 0, 10, 20, fakearg="fakearg")

        scenario._boot_server.assert_called_once_with("img", 0,
                                                      fakearg="fakearg")
        scenario.sleep_between.assert_called_once_with(10, 20)
        scenario._delete_server.assert_called_once_with(fake_server,
                                                        force=False)

    def test_boot_and_delete_multiple_servers(self):
        scenario = servers.NovaServers(self.context)
        scenario._boot_servers = mock.Mock()
        scenario._delete_servers = mock.Mock()
        scenario.sleep_between = mock.Mock()

        scenario.boot_and_delete_multiple_servers("img", "flavor", count=15,
                                                  min_sleep=10,
                                                  max_sleep=20,
                                                  fakearg="fakearg")

        scenario._boot_servers.assert_called_once_with("img", "flavor", 1,
                                                       instances_amount=15,
                                                       fakearg="fakearg")
        scenario.sleep_between.assert_called_once_with(10, 20)
        scenario._delete_servers.assert_called_once_with(
            scenario._boot_servers.return_value, force=False)

    def test_boot_and_list_server(self):
        scenario = servers.NovaServers(self.context)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._boot_server = mock.MagicMock()
        scenario._list_servers = mock.MagicMock()

        scenario.boot_and_list_server("img", 0, fakearg="fakearg")

        scenario._boot_server.assert_called_once_with("img", 0,
                                                      fakearg="fakearg")
        scenario._list_servers.assert_called_once_with(True)

    def test_suspend_and_resume_server(self):
        fake_server = object()

        scenario = servers.NovaServers(self.context)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario._suspend_server = mock.MagicMock()
        scenario._resume_server = mock.MagicMock()
        scenario._delete_server = mock.MagicMock()

        scenario.suspend_and_resume_server("img", 0, fakearg="fakearg")

        scenario._boot_server.assert_called_once_with("img", 0,
                                                      fakearg="fakearg")

        scenario._suspend_server.assert_called_once_with(fake_server)
        scenario._resume_server.assert_called_once_with(fake_server)
        scenario._delete_server.assert_called_once_with(fake_server,
                                                        force=False)

    def test_pause_and_unpause_server(self):
        fake_server = object()

        scenario = servers.NovaServers(self.context)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario._pause_server = mock.MagicMock()
        scenario._unpause_server = mock.MagicMock()
        scenario._delete_server = mock.MagicMock()

        scenario.pause_and_unpause_server("img", 0, fakearg="fakearg")

        scenario._boot_server.assert_called_once_with("img", 0,
                                                      fakearg="fakearg")

        scenario._pause_server.assert_called_once_with(fake_server)
        scenario._unpause_server.assert_called_once_with(fake_server)
        scenario._delete_server.assert_called_once_with(fake_server,
                                                        force=False)

    def test_shelve_and_unshelve_server(self):
        fake_server = mock.MagicMock()
        scenario = servers.NovaServers(self.context)
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario._shelve_server = mock.MagicMock()
        scenario._unshelve_server = mock.MagicMock()
        scenario._delete_server = mock.MagicMock()

        scenario.shelve_and_unshelve_server("img", 0, fakearg="fakearg")

        scenario._boot_server.assert_called_once_with("img", 0,
                                                      fakearg="fakearg")

        scenario._shelve_server.assert_called_once_with(fake_server)
        scenario._unshelve_server.assert_called_once_with(fake_server)
        scenario._delete_server.assert_called_once_with(fake_server,
                                                        force=False)

    def test_list_servers(self):
        scenario = servers.NovaServers(self.context)
        scenario._list_servers = mock.MagicMock()
        scenario.list_servers(True)
        scenario._list_servers.assert_called_once_with(True)

    def test_boot_server_from_volume_and_delete(self):
        fake_server = object()
        scenario = servers.NovaServers(self.context)
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario.sleep_between = mock.MagicMock()
        scenario._delete_server = mock.MagicMock()

        fake_volume = fakes.FakeVolumeManager().create()
        fake_volume.id = "volume_id"
        scenario._create_volume = mock.MagicMock(return_value=fake_volume)

        scenario.boot_server_from_volume_and_delete("img", 0, 5, 10, 20,
                                                    fakearg="f")

        scenario._create_volume.assert_called_once_with(5, imageRef="img")
        scenario._boot_server.assert_called_once_with(
            "img", 0,
            block_device_mapping={"vda": "volume_id:::1"},
            fakearg="f")
        scenario.sleep_between.assert_called_once_with(10, 20)
        scenario._delete_server.assert_called_once_with(fake_server,
                                                        force=False)

    def _prepare_boot(self, nic=None, assert_nic=False):
        fake_server = mock.MagicMock()

        scenario = servers.NovaServers(self.context)

        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario.generate_random_name = mock.MagicMock(return_value="name")

        kwargs = {"fakearg": "f"}
        expected_kwargs = {"fakearg": "f"}

        assert_nic = nic or assert_nic
        if nic:
            kwargs["nics"] = nic
        if assert_nic:
            self.clients("nova").networks.create("net-1")
            expected_kwargs["nics"] = nic or [{"net-id": "net-2"}]

        return scenario, kwargs, expected_kwargs

    def _verify_boot_server(self, nic=None, assert_nic=False):
        scenario, kwargs, expected_kwargs = self._prepare_boot(
            nic=nic, assert_nic=assert_nic)

        scenario.boot_server("img", 0, **kwargs)
        scenario._boot_server.assert_called_once_with(
            "img", 0, auto_assign_nic=False, **expected_kwargs)

    def test_boot_server_no_nics(self):
        self._verify_boot_server(nic=None, assert_nic=False)

    def test_boot_server_with_nic(self):
        self._verify_boot_server(nic=[{"net-id": "net-1"}], assert_nic=True)

    def test_snapshot_server(self):
        fake_server = object()
        fake_image = fakes.FakeImageManager()._create()
        fake_image.id = "image_id"

        scenario = servers.NovaServers(self.context)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario._create_image = mock.MagicMock(return_value=fake_image)
        scenario._delete_server = mock.MagicMock()
        scenario._delete_image = mock.MagicMock()

        scenario.snapshot_server("i", 0, fakearg=2)

        scenario._boot_server.assert_has_calls([
            mock.call("i", 0, fakearg=2),
            mock.call("image_id", 0, fakearg=2)])
        scenario._create_image.assert_called_once_with(fake_server)
        scenario._delete_server.assert_has_calls([
            mock.call(fake_server, force=False),
            mock.call(fake_server, force=False)])
        scenario._delete_image.assert_called_once_with(fake_image)

    def _test_resize(self, confirm=False):
        fake_server = object()
        fake_image = fakes.FakeImageManager()._create()
        fake_image.id = "image_id"
        flavor = mock.MagicMock()
        to_flavor = mock.MagicMock()

        scenario = servers.NovaServers(self.context)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario._resize_confirm = mock.MagicMock()
        scenario._resize_revert = mock.MagicMock()
        scenario._resize = mock.MagicMock()
        scenario._delete_server = mock.MagicMock()

        kwargs = {"confirm": confirm}
        scenario.resize_server(fake_image, flavor, to_flavor, **kwargs)

        scenario._resize.assert_called_once_with(fake_server, to_flavor)

        if confirm:
            scenario._resize_confirm.assert_called_once_with(fake_server)
        else:
            scenario._resize_revert.assert_called_once_with(fake_server)

    def test_resize_with_confirm(self):
        self._test_resize(confirm=True)

    def test_resize_with_revert(self):
        self._test_resize(confirm=False)

    @ddt.data({"confirm": True, "do_delete": True},
              {"confirm": False, "do_delete": True})
    @ddt.unpack
    def test_boot_server_attach_created_volume_and_resize(self, confirm=False,
                                                          do_delete=False):
        fake_volume = mock.MagicMock()
        fake_server = mock.MagicMock()
        flavor = mock.MagicMock()
        to_flavor = mock.MagicMock()

        scenario = servers.NovaServers(self.context)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario._create_volume = mock.MagicMock(return_value=fake_volume)
        scenario._attach_volume = mock.MagicMock()
        scenario._resize_confirm = mock.MagicMock()
        scenario._resize_revert = mock.MagicMock()
        scenario._resize = mock.MagicMock()
        scenario._detach_volume = mock.MagicMock()
        scenario._delete_volume = mock.MagicMock()
        scenario._delete_server = mock.MagicMock()
        scenario.sleep_between = mock.MagicMock()

        volume_size = 10
        scenario.boot_server_attach_created_volume_and_resize(
            "img", flavor, to_flavor, volume_size, min_sleep=10,
            max_sleep=20, confirm=confirm, do_delete=do_delete)

        scenario._boot_server.assert_called_once_with("img", flavor)
        scenario._create_volume.assert_called_once_with(volume_size)
        scenario._attach_volume.assert_called_once_with(fake_server,
                                                        fake_volume)
        scenario._detach_volume.assert_called_once_with(fake_server,
                                                        fake_volume)
        scenario.sleep_between.assert_called_once_with(10, 20)
        scenario._resize.assert_called_once_with(fake_server, to_flavor)

        if confirm:
            scenario._resize_confirm.assert_called_once_with(fake_server)
        else:
            scenario._resize_revert.assert_called_once_with(fake_server)

        if do_delete:
            scenario._detach_volume.assert_called_once_with(fake_server,
                                                            fake_volume)
            scenario._delete_volume.assert_called_once_with(fake_volume)
            scenario._delete_server.assert_called_once_with(fake_server,
                                                            force=False)

    @ddt.data({"confirm": True, "do_delete": True},
              {"confirm": False, "do_delete": True})
    @ddt.unpack
    def test_boot_server_from_volume_and_resize(self, confirm=False,
                                                do_delete=False):
        fake_server = object()
        flavor = mock.MagicMock()
        to_flavor = mock.MagicMock()
        scenario = servers.NovaServers(self.context)
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._resize_confirm = mock.MagicMock()
        scenario._resize_revert = mock.MagicMock()
        scenario._resize = mock.MagicMock()
        scenario.sleep_between = mock.MagicMock()
        scenario._delete_server = mock.MagicMock()

        fake_volume = fakes.FakeVolumeManager().create()
        fake_volume.id = "volume_id"
        scenario._create_volume = mock.MagicMock(return_value=fake_volume)

        volume_size = 10
        scenario.boot_server_from_volume_and_resize(
            "img", flavor, to_flavor, volume_size, min_sleep=10,
            max_sleep=20, confirm=confirm, do_delete=do_delete)

        scenario._create_volume.assert_called_once_with(10, imageRef="img")
        scenario._boot_server.assert_called_once_with(
            "img", flavor,
            block_device_mapping={"vda": "volume_id:::1"})
        scenario.sleep_between.assert_called_once_with(10, 20)
        scenario._resize.assert_called_once_with(fake_server, to_flavor)

        if confirm:
            scenario._resize_confirm.assert_called_once_with(fake_server)
        else:
            scenario._resize_revert.assert_called_once_with(fake_server)

        if do_delete:
            scenario._delete_server.assert_called_once_with(fake_server,
                                                            force=False)

    def test_boot_and_live_migrate_server(self):
        fake_server = mock.MagicMock()

        scenario = servers.NovaServers(self.context)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario.sleep_between = mock.MagicMock()
        scenario._find_host_to_migrate = mock.MagicMock(
            return_value="host_name")
        scenario._live_migrate = mock.MagicMock()
        scenario._delete_server = mock.MagicMock()

        scenario.boot_and_live_migrate_server("img", 0, min_sleep=10,
                                              max_sleep=20, fakearg="fakearg")

        scenario._boot_server.assert_called_once_with("img", 0,
                                                      fakearg="fakearg")

        scenario.sleep_between.assert_called_once_with(10, 20)

        scenario._find_host_to_migrate.assert_called_once_with(fake_server)

        scenario._live_migrate.assert_called_once_with(fake_server,
                                                       "host_name",
                                                       False, False)
        scenario._delete_server.assert_called_once_with(fake_server)

    def test_boot_server_from_volume_and_live_migrate(self):
        fake_server = mock.MagicMock()

        scenario = servers.NovaServers(self.context)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario.sleep_between = mock.MagicMock()
        scenario._find_host_to_migrate = mock.MagicMock(
            return_value="host_name")
        scenario._live_migrate = mock.MagicMock()
        scenario._delete_server = mock.MagicMock()

        fake_volume = fakes.FakeVolumeManager().create()
        fake_volume.id = "volume_id"
        scenario._create_volume = mock.MagicMock(return_value=fake_volume)

        scenario.boot_server_from_volume_and_live_migrate("img", 0, 5,
                                                          min_sleep=10,
                                                          max_sleep=20,
                                                          fakearg="f")

        scenario._create_volume.assert_called_once_with(5, imageRef="img")

        scenario._boot_server.assert_called_once_with(
            "img", 0,
            block_device_mapping={"vda": "volume_id:::1"},
            fakearg="f")

        scenario.sleep_between.assert_called_once_with(10, 20)

        scenario._find_host_to_migrate.assert_called_once_with(fake_server)

        scenario._live_migrate.assert_called_once_with(fake_server,
                                                       "host_name",
                                                       False, False)
        scenario._delete_server.assert_called_once_with(fake_server,
                                                        force=False)

    def test_boot_server_attach_created_volume_and_live_migrate(self):
        fake_volume = mock.MagicMock()
        fake_server = mock.MagicMock()

        scenario = servers.NovaServers(self.context)

        scenario._attach_volume = mock.MagicMock()
        scenario._detach_volume = mock.MagicMock()

        scenario.sleep_between = mock.MagicMock()

        scenario._find_host_to_migrate = mock.MagicMock(
            return_value="host_name")
        scenario._live_migrate = mock.MagicMock()

        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario._delete_server = mock.MagicMock()
        scenario._create_volume = mock.MagicMock(return_value=fake_volume)
        scenario._delete_volume = mock.MagicMock()

        image = "img"
        flavor = "flavor"
        size = 5
        boot_kwargs = {"some_var": "asd"}
        scenario.boot_server_attach_created_volume_and_live_migrate(
            image, flavor, size, min_sleep=10, max_sleep=20,
            boot_server_kwargs=boot_kwargs)
        scenario._boot_server.assert_called_once_with(image, flavor,
                                                      **boot_kwargs)
        scenario._create_volume.assert_called_once_with(size)
        scenario._attach_volume.assert_called_once_with(fake_server,
                                                        fake_volume)
        scenario._detach_volume.assert_called_once_with(fake_server,
                                                        fake_volume)
        scenario.sleep_between.assert_called_once_with(10, 20)
        scenario._live_migrate.assert_called_once_with(fake_server,
                                                       "host_name",
                                                       False, False)

        scenario._delete_volume.assert_called_once_with(fake_volume)
        scenario._delete_server.assert_called_once_with(fake_server)

    def _test_boot_and_migrate_server(self, confirm=False):
        fake_server = mock.MagicMock()

        scenario = servers.NovaServers(self.context)
        scenario.generate_random_name = mock.MagicMock(return_value="name")
        scenario._boot_server = mock.MagicMock(return_value=fake_server)
        scenario._stop_server = mock.MagicMock()
        scenario._migrate = mock.MagicMock()
        scenario._resize_confirm = mock.MagicMock()
        scenario._resize_revert = mock.MagicMock()
        scenario._delete_server = mock.MagicMock()

        kwargs = {"confirm": confirm}
        scenario.boot_and_migrate_server("img", 0,
                                         fakearg="fakearg", **kwargs)

        scenario._boot_server.assert_called_once_with("img", 0,
                                                      fakearg="fakearg",
                                                      confirm=confirm)

        scenario._stop_server.assert_called_once_with(fake_server)

        scenario._migrate.assert_called_once_with(fake_server)

        if confirm:
            scenario._resize_confirm.assert_called_once_with(fake_server,
                                                             status="SHUTOFF")
        else:
            scenario._resize_revert.assert_called_once_with(fake_server,
                                                            status="SHUTOFF")

        scenario._delete_server.assert_called_once_with(fake_server)

    def test_boot_and_migrate_server_with_confirm(self):
        self._test_boot_and_migrate_server(confirm=True)

    def test_boot_and_migrate_server_with_revert(self):
        self._test_boot_and_migrate_server(confirm=False)

    def test_boot_and_rebuild_server(self):
        scenario = servers.NovaServers(self.context)
        scenario._boot_server = mock.Mock()
        scenario._rebuild_server = mock.Mock()
        scenario._delete_server = mock.Mock()

        from_image = "img1"
        to_image = "img2"
        flavor = "flavor"
        scenario.boot_and_rebuild_server(from_image, to_image, flavor,
                                         fakearg="fakearg")

        scenario._boot_server.assert_called_once_with(from_image, flavor,
                                                      fakearg="fakearg")
        server = scenario._boot_server.return_value
        scenario._rebuild_server.assert_called_once_with(server, to_image)
        scenario._delete_server.assert_called_once_with(server)

    def test_boot_and_show_server(self):
        server = fakes.FakeServer()
        image = fakes.FakeImage()
        flavor = fakes.FakeFlavor()

        scenario = servers.NovaServers(self.context)
        scenario._boot_server = mock.MagicMock(return_value=server)
        scenario._show_server = mock.MagicMock()

        scenario.boot_and_show_server(image, flavor, fakearg="fakearg")

        scenario._boot_server.assert_called_once_with(image, flavor,
                                                      fakearg="fakearg")
        scenario._show_server.assert_called_once_with(server)

    @ddt.data({"length": None},
              {"length": 10})
    @ddt.unpack
    def test_boot_and_get_console_server(self, length):
        server = fakes.FakeServer()
        image = fakes.FakeImage()
        flavor = fakes.FakeFlavor()
        kwargs = {"fakearg": "fakearg"}

        scenario = servers.NovaServers(self.context)
        scenario._boot_server = mock.MagicMock(return_value=server)
        scenario._get_server_console_output = mock.MagicMock()

        scenario.boot_and_get_console_output(image, flavor, length,
                                             **kwargs)

        scenario._boot_server.assert_called_once_with(image, flavor,
                                                      **kwargs)
        scenario._get_server_console_output.assert_called_once_with(server,
                                                                    length)

    @mock.patch(NOVA_SERVERS_MODULE + ".network_wrapper.wrap")
    def test_boot_and_associate_floating_ip(self, mock_wrap):
        scenario = servers.NovaServers(self.context)
        server = mock.Mock()
        scenario._boot_server = mock.Mock(return_value=server)
        scenario._associate_floating_ip = mock.Mock()

        image = "img"
        flavor = "flavor"
        scenario.boot_and_associate_floating_ip(image, flavor,
                                                fakearg="fakearg")

        scenario._boot_server.assert_called_once_with(image, flavor,
                                                      fakearg="fakearg")
        net_wrap = mock_wrap.return_value
        net_wrap.create_floating_ip.assert_called_once_with(
            tenant_id=server.tenant_id)
        scenario._associate_floating_ip.assert_called_once_with(
            server, net_wrap.create_floating_ip.return_value["ip"])
