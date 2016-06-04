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
from rally.cli import envutils
from rally.common import db


class DBCommands(object):
    """Commands for DB management."""

    def recreate(self):
        """Drop and create Rally database.

        This will delete all existing data.
        """
        db.schema_cleanup()
        db.schema_create()
        envutils.clear_env()

    def create(self):
        """Create Rally database."""
        db.schema_create()

    def upgrade(self):
        """Upgrade Rally database to the latest state."""
        db.schema_upgrade()

    @cliutils.args("--revision",
                   help=("Downgrade to specified revision UUID. "
                         "Current revision of DB could be found by calling "
                         "'rally-manage db revision'"))
    def downgrade(self, revision):
        """Downgrade Rally database."""
        db.schema_downgrade(revision)

    def revision(self):
        """Print current Rally database revision UUID."""
        print(db.schema_revision())


def main():
    categories = {"db": DBCommands}
    return cliutils.run(sys.argv, categories)


if __name__ == "__main__":
    sys.exit(main())
