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

from rally.common import log as logging


LOG = logging.getLogger(__name__)


class DesignateQuotas(object):
    """Management of Designate quotas."""

    QUOTAS_SCHEMA = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "domains": {
                "type": "integer",
                "minimum": 1
            },
            "domain_recordsets": {
                "type": "integer",
                "minimum": 1
            },
            "domain_records": {
                "type": "integer",
                "minimum": 1
            },
            "recordset_records": {
                "type": "integer",
                "minimum": 1
            },
        }
    }

    def __init__(self, clients):
        self.clients = clients

    def update(self, tenant_id, **kwargs):
        self.clients.designate().quotas.update(tenant_id, kwargs)

    def delete(self, tenant_id):
        self.clients.designate().quotas.reset(tenant_id)
