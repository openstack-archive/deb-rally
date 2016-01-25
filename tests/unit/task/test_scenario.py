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

import traceback

import mock

from rally import consts
from rally import exceptions
from rally.task import context
from rally.task import scenario
from rally.task import validation
from tests.unit import fakes
from tests.unit import test


class ScenarioConfigureTestCase(test.TestCase):

    def test_configure(self):

        @scenario.configure("test_configure", "testing")
        def some_func():
            pass

        self.assertEqual("test_configure", some_func.get_name())
        self.assertEqual("testing", some_func.get_namespace())
        some_func.unregister()

    def test_configure_default_name(self):

        @scenario.configure(namespace="testing", context={"any": 42})
        def some_func():
            pass

        self.assertIsNone(some_func._meta_get("name"))
        self.assertEqual("testing", some_func.get_namespace())
        self.assertEqual({"any": 42}, some_func._meta_get("default_context"))
        some_func.unregister()

    def test_configure_cls(self):

        class ScenarioPluginCls(scenario.Scenario):

            @scenario.configure(namespace="any", context={"any": 43})
            def some(self):
                pass

        self.assertEqual("ScenarioPluginCls.some",
                         ScenarioPluginCls.some.get_name())
        self.assertEqual("any", ScenarioPluginCls.some.get_namespace())
        self.assertEqual({"any": 43},
                         ScenarioPluginCls.some._meta_get("default_context"))
        ScenarioPluginCls.some.unregister()


class ScenarioTestCase(test.TestCase):

    def test__validate_helper(self):
        validators = [
            mock.MagicMock(return_value=validation.ValidationResult(True)),
            mock.MagicMock(return_value=validation.ValidationResult(True))
        ]
        clients = mock.MagicMock()
        config = {"a": 1, "b": 2}
        deployment = mock.MagicMock()
        scenario.Scenario._validate_helper(validators, clients, config,
                                           deployment)
        for validator in validators:
            validator.assert_called_with(config, clients=clients,
                                         deployment=deployment)

    def test__validate_helper_somethingwent_wrong(self):
        validator = mock.MagicMock()
        validator.side_effect = Exception()

        self.assertRaises(exceptions.InvalidScenarioArgument,
                          scenario.Scenario._validate_helper,
                          [validator], "cl", "config", "deployment")
        validator.assert_called_once_with("config", clients="cl",
                                          deployment="deployment")

    def test__validate_helper__no_valid(self):
        validators = [
            mock.MagicMock(return_value=validation.ValidationResult(True)),
            mock.MagicMock(
                return_value=validation.ValidationResult(is_valid=False)
            )
        ]
        clients = mock.MagicMock()
        args = {"a": 1, "b": 2}
        self.assertRaises(exceptions.InvalidScenarioArgument,
                          scenario.Scenario._validate_helper,
                          validators, clients, args, "fake_uuid")

    @mock.patch("rally.task.scenario.Scenario.get")
    def test_validate__no_validators(self, mock_scenario_get):

        class Testing(fakes.FakeScenario):

            @scenario.configure()
            def validate__no_validators(self):
                pass

        mock_scenario_get.return_value = Testing.validate__no_validators
        scenario.Scenario.validate("Testing.validate__no_validators",
                                   {"a": 1, "b": 2})
        mock_scenario_get.assert_called_once_with(
            "Testing.validate__no_validators")
        Testing.validate__no_validators.unregister()

    @mock.patch("rally.task.scenario.Scenario._validate_helper")
    @mock.patch("rally.task.scenario.Scenario.get")
    def test_validate__admin_validators(self, mock_scenario_get,
                                        mock_scenario__validate_helper):

        class Testing(fakes.FakeScenario):

            @scenario.configure(namespace="testing")
            def validate_admin_validators(self):
                pass

        mock_scenario_get.return_value = Testing.validate_admin_validators

        validators = [mock.MagicMock(), mock.MagicMock()]
        for validator in validators:
            validator.permission = consts.EndpointPermission.ADMIN

        Testing.validate_admin_validators._meta_set(
            "validators", validators)
        deployment = mock.MagicMock()
        args = {"a": 1, "b": 2}
        scenario.Scenario.validate("Testing.validate_admin_validators",
                                   args, admin="admin", deployment=deployment)
        mock_scenario__validate_helper.assert_called_once_with(
            validators, "admin", args, deployment)

        Testing.validate_admin_validators.unregister()

    @mock.patch("rally.task.scenario.Scenario._validate_helper")
    @mock.patch("rally.task.scenario.Scenario.get")
    def test_validate_user_validators(self, mock_scenario_get,
                                      mock_scenario__validate_helper):

        class Testing(fakes.FakeScenario):

            @scenario.configure()
            def validate_user_validators(self):
                pass

        mock_scenario_get.return_value = Testing.validate_user_validators

        validators = [mock.MagicMock(), mock.MagicMock()]
        for validator in validators:
            validator.permission = consts.EndpointPermission.USER

        Testing.validate_user_validators._meta_set("validators", validators)
        args = {"a": 1, "b": 2}
        scenario.Scenario.validate(
            "Testing.validate_user_validators", args, users=["u1", "u2"])

        mock_scenario__validate_helper.assert_has_calls([
            mock.call(validators, "u1", args, None),
            mock.call(validators, "u2", args, None)
        ])

        Testing.validate_user_validators.unregister()

    def test_sleep_between_invalid_args(self):
        self.assertRaises(exceptions.InvalidArgumentsException,
                          scenario.Scenario().sleep_between, 15, 5)

        self.assertRaises(exceptions.InvalidArgumentsException,
                          scenario.Scenario().sleep_between, -1, 0)

        self.assertRaises(exceptions.InvalidArgumentsException,
                          scenario.Scenario().sleep_between, 0, -2)

    def test_sleep_between(self):
        scenario_inst = scenario.Scenario()
        scenario_inst.sleep_between(0.001, 0.002)
        self.assertTrue(0.001 <= scenario_inst.idle_duration() <= 0.002)

    def test_sleep_beetween_multi(self):
        scenario_inst = scenario.Scenario()
        scenario_inst.sleep_between(0.001, 0.001)
        scenario_inst.sleep_between(0.004, 0.004)
        self.assertEqual(scenario_inst.idle_duration(), 0.005)

    @mock.patch("rally.common.utils.interruptable_sleep")
    @mock.patch("rally.task.scenario.random.uniform")
    def test_sleep_between_internal(self, mock_uniform,
                                    mock_interruptable_sleep):
        scenario_inst = scenario.Scenario()

        mock_uniform.return_value = 1.5
        scenario_inst.sleep_between(1, 2)

        mock_interruptable_sleep.assert_called_once_with(
            mock_uniform.return_value, 0.1)
        self.assertEqual(scenario_inst.idle_duration(),
                         mock_uniform.return_value)

    def test_scenario_context_are_valid(self):
        for s in scenario.Scenario.get_all():
            try:
                context.ContextManager.validate(s._meta_get("default_context"))
            except Exception:
                print(traceback.format_exc())
                self.assertTrue(False,
                                "Scenario `%s` has wrong context" % scenario)

    def test_add_output(self):
        scenario_inst = scenario.Scenario()
        self.assertEqual({"additive": [], "complete": []},
                         scenario_inst._output)

        additive1 = {"title": "Additive 1", "chart_plugin": "Plugin1",
                     "description": "Foo description",
                     "data": [["foo", 1], ["bar", 2]]}
        additive2 = {"title": "Additive 2", "chart_plugin": "Plugin2",
                     "description": "Bar description",
                     "data": [["foo", 42], ["bar", 24]]}
        complete1 = {"title": "Complete 1", "chart_plugin": "Plugin3",
                     "description": "Complete description",
                     "data": [["ab", 1], ["cd", 2]]}
        complete2 = {"title": "Complete 2", "chart_plugin": "Plugin4",
                     "description": "Another complete description",
                     "data": [["vx", 1], ["yz", 2]]}

        scenario_inst.add_output(additive=additive1)
        self.assertEqual({"additive": [additive1], "complete": []},
                         scenario_inst._output)

        scenario_inst.add_output(complete=complete1)
        self.assertEqual({"additive": [additive1], "complete": [complete1]},
                         scenario_inst._output)

        scenario_inst.add_output(additive=additive2, complete=complete2)
        self.assertEqual({"additive": [additive1, additive2],
                          "complete": [complete1, complete2]},
                         scenario_inst._output)

    def test_add_output_raises(self):
        additive = {"title": "Foo title", "chart_plugin": "Plugin1",
                    "description": "Foo description",
                    "data": [["ab", 1], ["cd", 2]]}
        complete = {"title": "Bar title", "chart_plugin": "Plugin2",
                    "description": "Bar description",
                    "data": [["ef", 1], ["jh", 2]]}
        scenario_inst = scenario.Scenario()

        scenario_inst.add_output(additive=additive, complete=complete)

        for key in additive.keys():
            broken_additive = additive.copy()
            del broken_additive[key]
            self.assertRaises(exceptions.RallyException,
                              scenario_inst.add_output,
                              additive=broken_additive)

        for key in complete.keys():
            broken_complete = complete.copy()
            del broken_complete[key]
            self.assertRaises(exceptions.RallyException,
                              scenario_inst.add_output,
                              complete=broken_complete)
