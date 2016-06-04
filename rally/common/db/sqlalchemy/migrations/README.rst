..
      Copyright 2016 Mirantis Inc. All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

.. _db_migrations:

Database upgrade/downgrade in Rally
===================================

Information for users
---------------------

Rally supports DB schema versioning (schema versions are called *revisions*)
and migration (upgrade to later and downgrade to earlier revisions).

End user is provided with the following possibilities:

- Print current revision of DB.

  .. code-block:: shell

    rally-manage db revision

- Upgrade existing DB to the latest state.

  This is needed when previously existing Rally installation is being
  upgraded to a newer version. In this case user should issue command

  .. code-block:: shell

    rally-manage db upgrade

  **AFTER** upgrading Rally package. DB schema
  will get upgraded to the latest state and all existing data will be kept.

- Downgrade existing DB to a previous revision.

  This command could be useful if user wants to return to an earlier version
  of Rally. This could be done by issuing command

  .. code-block:: shell

    rally-manage db downgrade --revision <UUID>

  Database schema downgrade **MUST** be done **BEFORE** Rally package is downgraded.
  User must  provide revision UUID to which the schema must be downgraded.

Information for developers
--------------------------

DB migration in Rally is implemented via package *alembic*.

It is highly recommended to get familiar with it's documnetation
available by the link_ before proceeding.

.. _link: https://alembic.readthedocs.org

If developer is about to change existing DB schema they should
create new DB revision and migration script with the following command

.. code-block:: shell

  alembic --config rally/common/db/sqlalchemy/alembic.ini revision -m <Message>

It will generate migration script -- a file named `<UUID>_<Message>.py`
located in `rally/common/db/sqlalchemy/migrations/versions`.
Generated script should then be checked, edited if it is needed to be
and added to Rally source tree.
