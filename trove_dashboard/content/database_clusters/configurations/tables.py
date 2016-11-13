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

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from trove_dashboard import api


class AttachConfiguration(tables.LinkAction):
    name = "attach_configuration"
    verbose_name = _("Attach Configuration Group")
    url = "horizon:project:database_clusters:configurations:attach_config"
    classes = ("btn-attach-config", "ajax-modal")

    def allowed(self, request, cluster=None):
        return (cluster and cluster.task["name"] == 'NONE'
                and not hasattr(cluster, 'configuration'))


class DetachConfiguration(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Detach Configuration Group",
            u"Detach Configuration Groups",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Detached Configuration Group",
            u"Detached Configuration Groups",
            count
        )

    name = "detach_configuration"
    classes = ('btn-danger', 'btn-detach-config')

    def allowed(self, request, cluster=None):
        return (cluster and cluster.task["name"] == 'NONE'
                and hasattr(cluster, 'configuration'))

    def action(self, request, obj_id):
        api.trove.cluster_configuration_detach(request, obj_id)
