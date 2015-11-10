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
from oslo_config import cfg

from rally import exceptions as rally_exceptions
from rally.plugins.openstack.scenarios.nova import utils
from tests.unit import fakes
from tests.unit import test

BM_UTILS = "rally.task.utils"
NOVA_UTILS = "rally.plugins.openstack.scenarios.nova.utils"
CONF = cfg.CONF


@ddt.ddt
class NovaScenarioTestCase(test.ScenarioTestCase):

    def setUp(self):
        super(NovaScenarioTestCase, self).setUp()
        self.server = mock.Mock()
        self.server1 = mock.Mock()
        self.volume = mock.Mock()
        self.floating_ip = mock.Mock()
        self.image = mock.Mock()
        self.keypair = mock.Mock()
        self.context["iteration"] = 3
        self.context["config"] = {"users": {"tenants": 2}}

    def _context_with_networks(self, networks):
        retval = {"tenant": {"networks": networks}}
        retval.update(self.context)
        return retval

    def _context_with_secgroup(self, secgroup):
        retval = {"user": {"secgroup": secgroup,
                           "endpoint": mock.MagicMock()}}
        retval.update(self.context)
        return retval

    def test__list_servers(self):
        servers_list = []
        self.clients("nova").servers.list.return_value = servers_list
        nova_scenario = utils.NovaScenario(self.context)
        return_servers_list = nova_scenario._list_servers(True)
        self.assertEqual(servers_list, return_servers_list)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.list_servers")

    def test__pick_random_nic(self):
        context = {"tenant": {"networks": [{"id": "net_id_1"},
                                           {"id": "net_id_2"}]},
                   "iteration": 0}
        nova_scenario = utils.NovaScenario(context=context)
        nic1 = nova_scenario._pick_random_nic()
        self.assertEqual(nic1, [{"net-id": "net_id_1"}])

        context["iteration"] = 1
        nova_scenario = utils.NovaScenario(context=context)
        nic2 = nova_scenario._pick_random_nic()
        # balance to net 2
        self.assertEqual(nic2, [{"net-id": "net_id_2"}])

        context["iteration"] = 2
        nova_scenario = utils.NovaScenario(context=context)
        nic3 = nova_scenario._pick_random_nic()
        # balance again, get net 1
        self.assertEqual(nic3, [{"net-id": "net_id_1"}])

    @ddt.data(
        {},
        {"kwargs": {"auto_assign_nic": True}},
        {"kwargs": {"auto_assign_nic": True, "nics": [{"net-id": "baz_id"}]}},
        {"context": {"user": {"secgroup": {"name": "test"}}}},
        {"context": {"user": {"secgroup": {"name": "new"}}},
         "kwargs": {"security_groups": ["test"]}},
        {"context": {"user": {"secgroup": {"name": "test1"}}},
         "kwargs": {"security_groups": ["test1"]}},
    )
    @ddt.unpack
    def test__boot_server(self, context=None, kwargs=None):
        self.clients("nova").servers.create.return_value = self.server

        if context is None:
            context = self.context
        context.setdefault("user", {}).setdefault("endpoint", mock.MagicMock())
        context.setdefault("config", {})

        nova_scenario = utils.NovaScenario(context=context)
        nova_scenario._generate_random_name = mock.Mock()
        nova_scenario._pick_random_nic = mock.Mock()
        if kwargs is None:
            kwargs = {}
        kwargs["fakearg"] = "fakearg"
        return_server = nova_scenario._boot_server("image_id", "flavor_id",
                                                   **kwargs)
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_boot_poll_interval,
            timeout=CONF.benchmark.nova_server_boot_timeout)
        self.mock_resource_is.mock.assert_called_once_with("ACTIVE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self.assertEqual(self.mock_wait_for.mock.return_value, return_server)

        expected_kwargs = {"fakearg": "fakearg"}
        if "nics" in kwargs:
            expected_kwargs["nics"] = kwargs["nics"]
        elif "auto_assign_nic" in kwargs:
            expected_kwargs["nics"] = (nova_scenario._pick_random_nic.
                                       return_value)

        expected_secgroups = set()
        if "security_groups" in kwargs:
            expected_secgroups.update(kwargs["security_groups"])
        if "secgroup" in context["user"]:
            expected_secgroups.add(context["user"]["secgroup"]["name"])
        if expected_secgroups:
            expected_kwargs["security_groups"] = list(expected_secgroups)

        self.clients("nova").servers.create.assert_called_once_with(
            nova_scenario._generate_random_name.return_value,
            "image_id", "flavor_id", **expected_kwargs)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.boot_server")

    def test__boot_server_with_network_exception(self):
        self.clients("nova").servers.create.return_value = self.server
        nova_scenario = utils.NovaScenario(
            context=self._context_with_networks(None))
        self.assertRaises(TypeError, nova_scenario._boot_server,
                          "image_id", "flavor_id",
                          auto_assign_nic=True)

    def test__suspend_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._suspend_server(self.server)
        self.server.suspend.assert_called_once_with()
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_suspend_poll_interval,
            timeout=CONF.benchmark.nova_server_suspend_timeout)
        self.mock_resource_is.mock.assert_called_once_with("SUSPENDED")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.suspend_server")

    def test__resume_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._resume_server(self.server)
        self.server.resume.assert_called_once_with()
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_resume_poll_interval,
            timeout=CONF.benchmark.nova_server_resume_timeout)
        self.mock_resource_is.mock.assert_called_once_with("ACTIVE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.resume_server")

    def test__pause_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._pause_server(self.server)
        self.server.pause.assert_called_once_with()
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_pause_poll_interval,
            timeout=CONF.benchmark.nova_server_pause_timeout)
        self.mock_resource_is.mock.assert_called_once_with("PAUSED")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.pause_server")

    def test__unpause_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._unpause_server(self.server)
        self.server.unpause.assert_called_once_with()
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_unpause_poll_interval,
            timeout=CONF.benchmark.nova_server_unpause_timeout)
        self.mock_resource_is.mock.assert_called_once_with("ACTIVE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.unpause_server")

    def test__shelve_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._shelve_server(self.server)
        self.server.shelve.assert_called_once_with()
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_shelve_poll_interval,
            timeout=CONF.benchmark.nova_server_shelve_timeout)
        self.mock_resource_is.mock.assert_called_once_with("SHELVED_OFFLOADED")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.shelve_server")

    def test__unshelve_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._unshelve_server(self.server)
        self.server.unshelve.assert_called_once_with()
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_unshelve_poll_interval,
            timeout=CONF.benchmark.nova_server_unshelve_timeout)
        self.mock_resource_is.mock.assert_called_once_with("ACTIVE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.unshelve_server")

    def test__create_image(self):
        self.clients("nova").images.get.return_value = self.image
        nova_scenario = utils.NovaScenario(context=self.context)
        return_image = nova_scenario._create_image(self.server)
        self.mock_wait_for.mock.assert_called_once_with(
            self.image,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.
            nova_server_image_create_poll_interval,
            timeout=CONF.benchmark.nova_server_image_create_timeout)
        self.mock_resource_is.mock.assert_called_once_with("ACTIVE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self.assertEqual(self.mock_wait_for.mock.return_value, return_image)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.create_image")

    def test__default_delete_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._delete_server(self.server)
        self.server.delete.assert_called_once_with()
        self.mock_wait_for_delete.mock.assert_called_once_with(
            self.server,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_delete_poll_interval,
            timeout=CONF.benchmark.nova_server_delete_timeout)
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.delete_server")

    def test__force_delete_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._delete_server(self.server, force=True)
        self.server.force_delete.assert_called_once_with()
        self.mock_wait_for_delete.mock.assert_called_once_with(
            self.server,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_delete_poll_interval,
            timeout=CONF.benchmark.nova_server_delete_timeout)
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.force_delete_server")

    def test__reboot_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._reboot_server(self.server)
        self.server.reboot.assert_called_once_with(reboot_type="HARD")
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_reboot_poll_interval,
            timeout=CONF.benchmark.nova_server_reboot_timeout)
        self.mock_resource_is.mock.assert_called_once_with("ACTIVE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.reboot_server")

    def test__soft_reboot_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._soft_reboot_server(self.server)
        self.server.reboot.assert_called_once_with(reboot_type="SOFT")
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_reboot_poll_interval,
            timeout=CONF.benchmark.nova_server_reboot_timeout)
        self.mock_resource_is.mock.assert_called_once_with("ACTIVE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.soft_reboot_server")

    def test__rebuild_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._rebuild_server(self.server, "img", fakearg="fakearg")
        self.server.rebuild.assert_called_once_with("img", fakearg="fakearg")
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_rebuild_poll_interval,
            timeout=CONF.benchmark.nova_server_rebuild_timeout)
        self.mock_resource_is.mock.assert_called_once_with("ACTIVE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.rebuild_server")

    def test__start_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._start_server(self.server)
        self.server.start.assert_called_once_with()
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_start_poll_interval,
            timeout=CONF.benchmark.nova_server_start_timeout)
        self.mock_resource_is.mock.assert_called_once_with("ACTIVE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.start_server")

    def test__stop_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._stop_server(self.server)
        self.server.stop.assert_called_once_with()
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_stop_poll_interval,
            timeout=CONF.benchmark.nova_server_stop_timeout)
        self.mock_resource_is.mock.assert_called_once_with("SHUTOFF")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.stop_server")

    def test__rescue_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._rescue_server(self.server)
        self.server.rescue.assert_called_once_with()
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_rescue_poll_interval,
            timeout=CONF.benchmark.nova_server_rescue_timeout)
        self.mock_resource_is.mock.assert_called_once_with("RESCUE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.rescue_server")

    def test__unrescue_server(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._unrescue_server(self.server)
        self.server.unrescue.assert_called_once_with()
        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_unrescue_poll_interval,
            timeout=CONF.benchmark.nova_server_unrescue_timeout)
        self.mock_resource_is.mock.assert_called_once_with("ACTIVE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.unrescue_server")

    def _test_delete_servers(self, force=False):
        servers = [self.server, self.server1]
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._delete_servers(servers, force=force)
        check_interval = CONF.benchmark.nova_server_delete_poll_interval
        expected = []
        for server in servers:
            expected.append(mock.call(
                server,
                update_resource=self.mock_get_from_manager.mock.return_value,
                check_interval=check_interval,
                timeout=CONF.benchmark.nova_server_delete_timeout))
            if force:
                server.force_delete.assert_called_once_with()
                self.assertFalse(server.delete.called)
            else:
                server.delete.assert_called_once_with()
                self.assertFalse(server.force_delete.called)

        self.mock_wait_for_delete.mock.assert_has_calls(expected)
        timer_name = "nova.%sdelete_servers" % ("force_" if force else "")
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       timer_name)

    def test__default_delete_servers(self):
        self._test_delete_servers()

    def test__force_delete_servers(self):
        self._test_delete_servers(force=True)

    def test__delete_image(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._delete_image(self.image)
        self.image.delete.assert_called_once_with()
        self.mock_wait_for_delete.mock.assert_called_once_with(
            self.image,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.
            nova_server_image_delete_poll_interval,
            timeout=CONF.benchmark.nova_server_image_delete_timeout)
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.delete_image")

    @ddt.data(
        {"requests": 1},
        {"requests": 25},
        {"requests": 2, "name_prefix": "foo", "instances_amount": 100,
         "auto_assign_nic": True, "fakearg": "fake"},
        {"auto_assign_nic": True, "nics": [{"net-id": "foo"}]},
        {"auto_assign_nic": False, "nics": [{"net-id": "foo"}]})
    @ddt.unpack
    def test__boot_servers(self, image_id="image", flavor_id="flavor",
                           requests=1, name_prefix=None, instances_amount=1,
                           auto_assign_nic=False, **kwargs):
        servers = [mock.Mock() for i in range(instances_amount)]
        self.clients("nova").servers.list.return_value = servers
        scenario = utils.NovaScenario(context=self.context)
        scenario._generate_random_name = mock.Mock()
        scenario._pick_random_nic = mock.Mock()

        scenario._boot_servers(image_id, flavor_id, requests,
                               name_prefix=name_prefix,
                               instances_amount=instances_amount,
                               auto_assign_nic=auto_assign_nic,
                               **kwargs)

        expected_kwargs = dict(kwargs)
        if auto_assign_nic and "nics" not in kwargs:
            expected_kwargs["nics"] = scenario._pick_random_nic.return_value

        if name_prefix is None:
            name_prefix = scenario._generate_random_name.return_value

        create_calls = [
            mock.call("%s_%d" % (name_prefix, i), image_id, flavor_id,
                      min_count=instances_amount, max_count=instances_amount,
                      **expected_kwargs)
            for i in range(requests)]
        self.clients("nova").servers.create.assert_has_calls(create_calls)

        wait_for_calls = [
            mock.call(
                servers[i],
                is_ready=self.mock_resource_is.mock.return_value,
                update_resource=self.mock_get_from_manager.mock.return_value,
                check_interval=CONF.benchmark.nova_server_boot_poll_interval,
                timeout=CONF.benchmark.nova_server_boot_timeout)
            for i in range(instances_amount)]
        self.mock_wait_for.mock.assert_has_calls(wait_for_calls)

        self.mock_resource_is.mock.assert_has_calls([
            mock.call("ACTIVE") for i in range(instances_amount)])
        self.mock_get_from_manager.mock.assert_has_calls(
            [mock.call() for i in range(instances_amount)])
        self._test_atomic_action_timer(scenario.atomic_actions(),
                                       "nova.boot_servers")

    def test__associate_floating_ip(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._associate_floating_ip(self.server, self.floating_ip)
        self.server.add_floating_ip.assert_called_once_with(self.floating_ip,
                                                            fixed_address=None)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.associate_floating_ip")

    def test__dissociate_floating_ip(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._dissociate_floating_ip(self.server, self.floating_ip)
        self.server.remove_floating_ip.assert_called_once_with(
            self.floating_ip)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.dissociate_floating_ip")

    def test__check_ip_address(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        fake_server = fakes.FakeServerManager().create("test_server",
                                                       "image_id_01",
                                                       "flavor_id_01")
        fake_server.addresses = {
            "private": [
                {"version": 4, "addr": "1.2.3.4"},
            ]}
        floating_ip = fakes.FakeFloatingIP()
        floating_ip.ip = "10.20.30.40"

        # Also test function check_ip_address accept a string as attr
        self.assertFalse(
            nova_scenario.check_ip_address(floating_ip.ip)(fake_server))
        self.assertTrue(
            nova_scenario.check_ip_address(floating_ip.ip, must_exist=False)
            (fake_server))

        fake_server.addresses["private"].append(
            {"version": 4, "addr": floating_ip.ip}
        )
        # Also test function check_ip_address accept an object with attr ip
        self.assertTrue(
            nova_scenario.check_ip_address(floating_ip)
            (fake_server))
        self.assertFalse(
            nova_scenario.check_ip_address(floating_ip, must_exist=False)
            (fake_server))

    def test__list_networks(self):
        network_list = []
        self.clients("nova").networks.list.return_value = network_list
        nova_scenario = utils.NovaScenario(context=self.context)
        return_network_list = nova_scenario._list_networks()
        self.assertEqual(network_list, return_network_list)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.list_networks")

    def test__resize(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        to_flavor = mock.Mock()
        nova_scenario._resize(self.server, to_flavor)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.resize")

    def test__resize_confirm(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._resize_confirm(self.server)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.resize_confirm")

    def test__resize_revert(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._resize_revert(self.server)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.resize_revert")

    def test__attach_volume(self):
        self.clients("nova").volumes.create_server_volume.return_value = None
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._attach_volume(self.server, self.volume)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.attach_volume")

    def test__detach_volume(self):
        self.clients("nova").volumes.delete_server_volume.return_value = None
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._detach_volume(self.server, self.volume)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.detach_volume")

    def test__live_migrate_server(self):
        fake_host = mock.MagicMock()
        self.admin_clients("nova").servers.get(return_value=self.server)
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._live_migrate(self.server,
                                    fake_host,
                                    block_migration=False,
                                    disk_over_commit=False,
                                    skip_host_check=True)

        self.mock_wait_for.mock.assert_called_once_with(
            self.server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.
            nova_server_live_migrate_poll_interval,
            timeout=CONF.benchmark.nova_server_live_migrate_timeout)
        self.mock_resource_is.mock.assert_called_once_with("ACTIVE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.live_migrate")

    def test__find_host_to_migrate(self):
        fake_server = self.server
        fake_host = {"nova-compute": {"available": True}}
        self.admin_clients("nova").servers.get.return_value = fake_server
        self.admin_clients("nova").availability_zones.list.return_value = [
            mock.MagicMock(zoneName="a",
                           hosts={"a1": fake_host, "a2": fake_host,
                                  "a3": fake_host}),
            mock.MagicMock(zoneName="b",
                           hosts={"b1": fake_host, "b2": fake_host,
                                  "b3": fake_host}),
            mock.MagicMock(zoneName="c",
                           hosts={"c1": fake_host,
                                  "c2": fake_host, "c3": fake_host})
        ]
        setattr(fake_server, "OS-EXT-SRV-ATTR:host", "b2")
        setattr(fake_server, "OS-EXT-AZ:availability_zone", "b")
        nova_scenario = utils.NovaScenario(context=self.context)

        self.assertIn(
            nova_scenario._find_host_to_migrate(fake_server), ["b1", "b3"])

    def test__migrate_server(self):
        fake_server = self.server
        setattr(fake_server, "OS-EXT-SRV-ATTR:host", "a1")
        self.clients("nova").servers.get(return_value=fake_server)
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._migrate(fake_server, skip_host_check=True)

        self.mock_wait_for.mock.assert_called_once_with(
            fake_server,
            is_ready=self.mock_resource_is.mock.return_value,
            update_resource=self.mock_get_from_manager.mock.return_value,
            check_interval=CONF.benchmark.nova_server_migrate_poll_interval,
            timeout=CONF.benchmark.nova_server_migrate_timeout)
        self.mock_resource_is.mock.assert_called_once_with("VERIFY_RESIZE")
        self.mock_get_from_manager.mock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.migrate")

        self.assertRaises(rally_exceptions.MigrateException,
                          nova_scenario._migrate,
                          fake_server, skip_host_check=False)

    def test__create_security_groups(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._generate_random_name = mock.MagicMock()

        security_group_count = 5

        sec_groups = nova_scenario._create_security_groups(
            security_group_count)

        self.assertEqual(security_group_count, len(sec_groups))
        self.assertEqual(security_group_count,
                         nova_scenario._generate_random_name.call_count)
        self.assertEqual(
            security_group_count,
            self.clients("nova").security_groups.create.call_count)
        self._test_atomic_action_timer(
            nova_scenario.atomic_actions(),
            "nova.create_%s_security_groups" % security_group_count)

    def test__create_rules_for_security_group(self):
        nova_scenario = utils.NovaScenario(context=self.context)

        fake_secgroups = [fakes.FakeSecurityGroup(None, None, 1, "uuid1"),
                          fakes.FakeSecurityGroup(None, None, 2, "uuid2")]
        rules_per_security_group = 10

        nova_scenario._create_rules_for_security_group(
            fake_secgroups, rules_per_security_group)

        self.assertEqual(
            len(fake_secgroups) * rules_per_security_group,
            self.clients("nova").security_group_rules.create.call_count)
        self._test_atomic_action_timer(
            nova_scenario.atomic_actions(),
            "nova.create_%s_rules" %
            (rules_per_security_group * len(fake_secgroups)))

    def test__update_security_groups(self):
        nova_scenario = utils.NovaScenario()
        fake_secgroups = [fakes.FakeSecurityGroup(None, None, 1, "uuid1"),
                          fakes.FakeSecurityGroup(None, None, 2, "uuid2")]
        nova_scenario._update_security_groups(fake_secgroups)
        self.assertEqual(
            len(fake_secgroups),
            self.clients("nova").security_groups.update.call_count)
        self._test_atomic_action_timer(
            nova_scenario.atomic_actions(),
            "nova.update_%s_security_groups" % len(fake_secgroups))

    def test__delete_security_groups(self):
        nova_scenario = utils.NovaScenario(context=self.context)

        fake_secgroups = [fakes.FakeSecurityGroup(None, None, 1, "uuid1"),
                          fakes.FakeSecurityGroup(None, None, 2, "uuid2")]

        nova_scenario._delete_security_groups(fake_secgroups)

        self.assertSequenceEqual(
            map(lambda x: mock.call(x.id), fake_secgroups),
            self.clients("nova").security_groups.delete.call_args_list)
        self._test_atomic_action_timer(
            nova_scenario.atomic_actions(),
            "nova.delete_%s_security_groups" % len(fake_secgroups))

    def test__list_security_groups(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._list_security_groups()

        self.clients("nova").security_groups.list.assert_called_once_with()

        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.list_security_groups")

    def test__list_keypairs(self):
        keypairs_list = ["foo_keypair"]
        self.clients("nova").keypairs.list.return_value = keypairs_list
        nova_scenario = utils.NovaScenario(context=self.context)
        return_keypairs_list = nova_scenario._list_keypairs()
        self.assertEqual(keypairs_list, return_keypairs_list)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.list_keypairs")

    def test__create_keypair(self):
        self.clients("nova").keypairs.create.return_value.name = self.keypair
        nova_scenario = utils.NovaScenario(context=self.context)
        return_keypair = nova_scenario._create_keypair()
        self.assertEqual(self.keypair, return_keypair)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.create_keypair")

    def test__delete_keypair(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._delete_keypair(self.keypair)
        self.clients("nova").keypairs.delete.assert_called_once_with(
            self.keypair)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.delete_keypair")

    def test__list_floating_ips_bulk(self):
        floating_ips_bulk_list = ["foo_floating_ips_bulk"]
        self.admin_clients("nova").floating_ips_bulk.list.return_value = (
            floating_ips_bulk_list)
        nova_scenario = utils.NovaScenario(context=self.context)
        return_floating_ips_bulk_list = nova_scenario._list_floating_ips_bulk()
        self.assertEqual(floating_ips_bulk_list, return_floating_ips_bulk_list)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.list_floating_ips_bulk")

    @mock.patch(NOVA_UTILS + ".network_wrapper.generate_cidr")
    def test__create_floating_ips_bulk(self, mock_generate_cidr):
        fake_cidr = "10.2.0.0/24"
        fake_pool = "test1"
        fake_floating_ips_bulk = mock.MagicMock()
        fake_floating_ips_bulk.ip_range = fake_cidr
        fake_floating_ips_bulk.pool = fake_pool
        self.admin_clients("nova").floating_ips_bulk.create.return_value = (
            fake_floating_ips_bulk)
        nova_scenario = utils.NovaScenario(context=self.context)
        return_iprange = nova_scenario._create_floating_ips_bulk(fake_cidr)
        mock_generate_cidr.assert_called_once_with(start_cidr=fake_cidr)
        self.assertEqual(return_iprange, fake_floating_ips_bulk)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.create_floating_ips_bulk")

    def test__delete_floating_ips_bulk(self):
        fake_cidr = "10.2.0.0/24"
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._delete_floating_ips_bulk(fake_cidr)
        self.admin_clients(
            "nova").floating_ips_bulk.delete.assert_called_once_with(fake_cidr)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.delete_floating_ips_bulk")

    def test__list_hypervisors(self):
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._list_hypervisors(detailed=False)
        self.admin_clients("nova").hypervisors.list.assert_called_once_with(
            False)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.list_hypervisors")

    def test__list_images(self):
        nova_scenario = utils.NovaScenario()
        nova_scenario._list_images(detailed=False, fakearg="fakearg")
        self.clients("nova").images.list.assert_called_once_with(
            False, fakearg="fakearg")
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.list_images")

    def test__lock_server(self):
        server = mock.Mock()
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._lock_server(server)
        server.lock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.lock_server")

    def test__unlock_server(self):
        server = mock.Mock()
        nova_scenario = utils.NovaScenario(context=self.context)
        nova_scenario._unlock_server(server)
        server.unlock.assert_called_once_with()
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.unlock_server")

    def test__delete_network(self):
        fake_netlabel = "test1"
        nova_scenario = utils.NovaScenario()
        nova_scenario._delete_network(fake_netlabel)
        self.admin_clients("nova").networks.delete.assert_called_once_with(
            fake_netlabel)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.delete_network")

    @mock.patch(NOVA_UTILS + ".network_wrapper.generate_cidr")
    def test__create_network(self, mock_generate_cidr):
        fake_cidr = "10.2.0.0/24"
        fake_net = mock.MagicMock()
        fake_net.cidr = fake_cidr
        self.admin_clients("nova").networks.create.return_value = (fake_net)

        nova_scenario = utils.NovaScenario()
        nova_scenario._generate_random_name = mock.Mock(
            return_value="rally_novanet_fake")

        return_netlabel = nova_scenario._create_network(fake_cidr,
                                                        fakearg="fakearg")
        mock_generate_cidr.assert_called_once_with(start_cidr=fake_cidr)
        self.admin_clients("nova").networks.create.assert_called_once_with(
            label="rally_novanet_fake", cidr=mock_generate_cidr.return_value,
            fakearg="fakearg")
        self.assertEqual(return_netlabel, fake_net)
        self._test_atomic_action_timer(nova_scenario.atomic_actions(),
                                       "nova.create_network")
