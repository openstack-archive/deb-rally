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

""" CLI interface for Rally. """

from __future__ import print_function

import sys

from rally.cli import cliutils
from rally.cli.commands import deployment
from rally.cli.commands import info
from rally.cli.commands import plugin
from rally.cli.commands import show
from rally.cli.commands import task
from rally.cli.commands import verify


categories = {
    "deployment": deployment.DeploymentCommands,
    "info": info.InfoCommands,
    "plugin": plugin.PluginCommands,
    "show": show.ShowCommands,
    "task": task.TaskCommands,
    "verify": verify.VerifyCommands
}


def main():
    return cliutils.run(sys.argv, categories)

if __name__ == "__main__":
    main()
