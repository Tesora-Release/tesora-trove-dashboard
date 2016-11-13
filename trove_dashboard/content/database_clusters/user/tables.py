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
from django.template import defaultfilters as d_filters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from trove_dashboard import api
from trove_dashboard.content.databases import tables as databases_tables


class CreateUser(tables.LinkAction):
    name = "create_user"
    verbose_name = _("Create User")
    url = "horizon:project:database_clusters:user:create_user"
    classes = ("ajax-modal",)
    icon = "plus"

    def allowed(self, request, instance=None):
        return databases_tables.has_user_add_perm(request)

    def get_link_url(self, datum=None):
        cluster_id = self.table.kwargs['cluster_id']
        return urlresolvers.reverse(self.url, args=[cluster_id])


class DeleteUser(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete User",
            u"Delete Users",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted User",
            u"Deleted Users",
            count
        )

    name = "delete_user"

    def delete(self, request, obj_id):
        user = self.table.get_object_by_id(obj_id)
        api.trove.user_delete(request, self.table.kwargs['cluster_id'],
                              user.name,
                              host=user.host)


class EditUser(tables.LinkAction):
    name = "edit_user"
    verbose_name = _("Edit User")
    url = "horizon:project:database_clusters:user:edit_user"
    classes = ("ajax-modal",)
    icon = "pencil"

    def allowed(self, request, cluster=None):
        return databases_tables.has_user_add_perm(request)

    def get_link_url(self, datum):
        user = datum
        return urlresolvers.reverse(self.url,
                                    args=[self.table.kwargs['cluster_id'],
                                          user.name,
                                          user.host])


class ManageUsers(tables.LinkAction):
    name = "manage_users"
    verbose_name = _("Manage Users")
    url = "horizon:project:database_clusters:user:manage_users"

    def allowed(self, request, cluster=None):
        if cluster and cluster.task["name"] == 'NONE':
            return True
        return False

    def get_link_url(self, datum):
        return urlresolvers.reverse(self.url, args=[datum.id])


class ManageAccess(tables.LinkAction):
    name = "manage_access"
    verbose_name = _("Manage Access")
    url = "horizon:project:database_clusters:user:access_detail"
    icon = "pencil"

    def allowed(self, request, cluster=None):
        return databases_tables.has_user_add_perm(request)

    def get_link_url(self, datum):
        user = datum
        return urlresolvers.reverse(self.url,
                                    args=[self.table.kwargs['cluster_id'],
                                          user.name,
                                          user.host])


class UsersTable(databases_tables.UsersTable):
    class Meta(object):
        table_actions = (CreateUser, DeleteUser)
        row_actions = (ManageAccess, EditUser, DeleteUser)


class GrantAccess(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Grant Access",
            u"Grant Access",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Granted Access to",
            u"Granted Access to",
            count
        )

    name = "grant_access"
    classes = ('btn-grant-access')

    def allowed(self, request, instance=None):
        if instance:
            return not instance.access
        return False

    def action(self, request, obj_id):
        api.trove.user_grant_access(
            request,
            self.table.kwargs['cluster_id'],
            self.table.kwargs['user_name'],
            [obj_id],
            host=self.table.kwargs['user_host'])


class RevokeAccess(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Revoke Access",
            u"Revoke Access",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Access Revoked to",
            u"Access Revoked to",
            count
        )

    name = "revoke_access"
    classes = ('btn-revoke-access')

    def allowed(self, request, instance=None):
        if instance:
            return instance.access
        return False

    def action(self, request, obj_id):
        api.trove.user_revoke_access(
            request,
            self.table.kwargs['cluster_id'],
            self.table.kwargs['user_name'],
            obj_id,
            host=self.table.kwargs['user_host'])


class AccessTable(tables.DataTable):
    dbname = tables.Column("name", verbose_name=_("Name"))
    access = tables.Column(
        "access",
        verbose_name=_("Accessible"),
        filters=(d_filters.yesno, d_filters.capfirst))

    class Meta(object):
        name = "access"
        verbose_name = _("Database Access")
        row_actions = (GrantAccess, RevokeAccess)

    def get_object_id(self, datum):
        return datum.name
