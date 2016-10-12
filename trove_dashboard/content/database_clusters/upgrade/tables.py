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

from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from trove_dashboard import api


class UpgradeCluster(tables.LinkAction):
    name = "upgrade_cluster_action"
    verbose_name = _("Upgrade Cluster")
    url = "horizon:project:database_clusters:upgrade:upgrade_cluster"
    classes = ("ajax-modal",)

    def allowed(self, request, cluster):
        if cluster and cluster.task["name"] == 'NONE':
            datastore_version_list = api.trove.datastore_version_list(
                request, cluster.datastore['type'])
            if datastore_version_list:
                for dsv in datastore_version_list:
                    if cluster.datastore['version'] != dsv.name:
                        return True
        return False

    def get_link_url(self, datum):
        cluster_id = self.table.get_object_id(datum)
        return urlresolvers.reverse(self.url, args=[cluster_id])
