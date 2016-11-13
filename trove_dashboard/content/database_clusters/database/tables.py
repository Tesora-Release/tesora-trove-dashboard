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
from django.utils.translation import ungettext_lazy

from horizon import tables

from trove_dashboard import api
from trove_dashboard.content.databases import tables as databases_tables


class CreateDatabase(tables.LinkAction):
    name = "create_database"
    verbose_name = _("Create Database")
    url = "horizon:project:database_clusters:database:create_database"
    classes = ("ajax-modal",)
    icon = "plus"

    def allowed(self, request, instance=None):
        return databases_tables.has_database_add_perm(request)

    def get_link_url(self, datum=None):
        cluster_id = self.table.kwargs['cluster_id']
        return urlresolvers.reverse(self.url, args=[cluster_id])


class DeleteDatabase(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Database",
            u"Delete Databases",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Database",
            u"Deleted Databases",
            count
        )

    def delete(self, request, obj_id):
        database = self.table.get_object_by_id(obj_id)
        api.trove.database_delete(request,
                                  self.table.kwargs['cluster_id'],
                                  database.name)


class ManageDatabases(tables.LinkAction):
    name = "manage_databases"
    verbose_name = _("Manage Databases")
    url = "horizon:project:database_clusters:database:manage_databases"

    def allowed(self, request, cluster=None):
        if cluster and cluster.task["name"] == 'NONE':
            return True
        return False

    def get_link_url(self, datum):
        return urlresolvers.reverse(self.url, args=[datum.id])


class DatabasesTable(databases_tables.DatabaseTable):
    class Meta(object):
        table_actions = (CreateDatabase, DeleteDatabase,)
        row_actions = (DeleteDatabase,)
