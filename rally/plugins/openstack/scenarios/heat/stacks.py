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

from rally import consts
from rally.plugins.openstack import scenario
from rally.plugins.openstack.scenarios.heat import utils
from rally.task import atomic
from rally.task import types
from rally.task import validation


class HeatStacks(utils.HeatScenario):
    """Benchmark scenarios for Heat stacks."""

    @types.set(template_path=types.FileType, files=types.FileTypeDict)
    @validation.required_services(consts.Service.HEAT)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["heat"]})
    def create_and_list_stack(self, template_path, parameters=None,
                              files=None, environment=None):
        """Create a stack and then list all stacks.

        Measure the "heat stack-create" and "heat stack-list" commands
        performance.

        :param template_path: path to stack template file
        :param parameters: parameters to use in heat template
        :param files: files used in template
        :param environment: stack environment definition
        """
        self._create_stack(template_path, parameters, files, environment)
        self._list_stacks()

    @validation.required_services(consts.Service.HEAT)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def list_stacks_and_resources(self):
        """List all resources from tenant stacks."""

        stacks = self._list_stacks()
        with atomic.ActionTimer(
                self, "heat.list_resources_of_%s_stacks" % len(stacks)):
            for stack in stacks:
                self.clients("heat").resources.list(stack.id)

    @types.set(template_path=types.FileType, files=types.FileTypeDict)
    @validation.required_services(consts.Service.HEAT)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["heat"]})
    def create_and_delete_stack(self, template_path, parameters=None,
                                files=None, environment=None):
        """Create and then delete a stack.

        Measure the "heat stack-create" and "heat stack-delete" commands
        performance.

        :param template_path: path to stack template file
        :param parameters: parameters to use in heat template
        :param files: files used in template
        :param environment: stack environment definition
        """

        stack = self._create_stack(template_path, parameters,
                                   files, environment)
        self._delete_stack(stack)

    @types.set(template_path=types.FileType, files=types.FileTypeDict)
    @validation.required_services(consts.Service.HEAT)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["heat"]})
    def create_check_delete_stack(self, template_path, parameters=None,
                                  files=None, environment=None):
        """Create, check and delete a stack.

        Measure the performance of the following commands:
        - heat stack-create
        - heat action-check
        - heat stack-delete

        :param template_path: path to stack template file
        :param parameters: parameters to use in heat template
        :param files: files used in template
        :param environment: stack environment definition
        """

        stack = self._create_stack(template_path, parameters,
                                   files, environment)
        self._check_stack(stack)
        self._delete_stack(stack)

    @types.set(template_path=types.FileType,
               updated_template_path=types.FileType,
               files=types.FileTypeDict,
               updated_files=types.FileTypeDict)
    @validation.required_services(consts.Service.HEAT)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["heat"]})
    def create_update_delete_stack(self, template_path,
                                   updated_template_path,
                                   parameters=None, updated_parameters=None,
                                   files=None, updated_files=None,
                                   environment=None, updated_environment=None):
        """Create, update and then delete a stack.

        Measure the "heat stack-create", "heat stack-update"
        and "heat stack-delete" commands performance.

        :param template_path: path to stack template file
        :param updated_template_path: path to updated stack template file
        :param parameters: parameters to use in heat template
        :param updated_parameters: parameters to use in updated heat template
                                   If not specified then parameters will be
                                   used instead
        :param files: files used in template
        :param updated_files: files used in updated template. If not specified
                              files value will be used instead
        :param environment: stack environment definition
        :param updated_environment: environment definition for updated stack
        """

        stack = self._create_stack(template_path, parameters,
                                   files, environment)
        self._update_stack(stack, updated_template_path,
                           updated_parameters or parameters,
                           updated_files or files,
                           updated_environment or environment)
        self._delete_stack(stack)

    @types.set(template_path=types.FileType, files=types.FileTypeDict)
    @validation.required_services(consts.Service.HEAT)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["heat"]})
    def create_stack_and_scale(self, template_path, output_key, delta,
                               parameters=None, files=None,
                               environment=None):
        """Create an autoscaling stack and invoke a scaling policy.

        Measure the performance of autoscaling webhooks.

        :param template_path: path to template file that includes an
                              OS::Heat::AutoScalingGroup resource
        :param output_key: the stack output key that corresponds to
                           the scaling webhook
        :param delta: the number of instances the stack is expected to
                      change by.
        :param parameters: parameters to use in heat template
        :param files: files used in template (dict of file name to
                      file path)
        :param environment: stack environment definition (dict)
        """
        # TODO(stpierre): Kilo Heat is *much* better than Juno for the
        # requirements of this scenario, so once Juno goes out of
        # support we should update this scenario to suck less. Namely:
        #
        # * Kilo Heat can supply alarm_url attributes without needing
        #   an output key, so instead of getting the output key from
        #   the user, just get the name of the ScalingPolicy to apply.
        # * Kilo Heat changes the status of a stack while scaling it,
        #   so _scale_stack() can check for the stack to have changed
        #   size and for it to be in UPDATE_COMPLETE state, so the
        #   user no longer needs to specify the expected delta.
        stack = self._create_stack(template_path, parameters, files,
                                   environment)
        self._scale_stack(stack, output_key, delta)

    @types.set(template_path=types.FileType, files=types.FileTypeDict)
    @validation.required_services(consts.Service.HEAT)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["heat"]})
    def create_suspend_resume_delete_stack(self, template_path,
                                           parameters=None, files=None,
                                           environment=None):
        """Create, suspend-resume and then delete a stack.

        Measure performance of the following commands:
        heat stack-create
        heat action-suspend
        heat action-resume
        heat stack-delete

        :param template_path: path to stack template file
        :param parameters: parameters to use in heat template
        :param files: files used in template
        :param environment: stack environment definition
        """

        s = self._create_stack(template_path, parameters, files, environment)
        self._suspend_stack(s)
        self._resume_stack(s)
        self._delete_stack(s)

    @validation.required_services(consts.Service.HEAT)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def list_stacks_and_events(self):
        """List events from tenant stacks."""

        stacks = self._list_stacks()
        with atomic.ActionTimer(
                self, "heat.list_events_of_%s_stacks" % len(stacks)):
            for stack in stacks:
                self.clients("heat").events.list(stack.id)

    @types.set(template_path=types.FileType, files=types.FileTypeDict)
    @validation.required_services(consts.Service.HEAT)
    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["heat"]})
    def create_snapshot_restore_delete_stack(self, template_path,
                                             parameters=None, files=None,
                                             environment=None):
        """Create, snapshot-restore and then delete a stack.

        Measure performance of the following commands:
        heat stack-create
        heat stack-snapshot
        heat stack-restore
        heat stack-delete

        :param template_path: path to stack template file
        :param parameters: parameters to use in heat template
        :param files: files used in template
        :param environment: stack environment definition
        """

        stack = self._create_stack(
            template_path, parameters, files, environment)
        snapshot = self._snapshot_stack(stack)
        self._restore_stack(stack, snapshot["id"])
        self._delete_stack(stack)
