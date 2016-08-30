# Copyright 2016 Tesora Inc.
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

import logging

from django.utils.translation import ugettext_lazy as _

from trove_dashboard.content.databases import tables as database_tables

LOG = logging.getLogger(__name__)


class MastersTable(database_tables.InstancesTable):
    class Meta(object):
        name = "masters_table"
        verbose_name = _("Masters")
        row_actions = (database_tables.ViewReplicas,
                       database_tables.EjectReplicaSource)


class ReplicasTable(database_tables.InstancesTable):
    class Meta(object):
        name = "replicas_table"
        verbose_name = _("Replicas")
        row_actions = (database_tables.PromoteToReplicaSource,
                       database_tables.DetachReplica)
