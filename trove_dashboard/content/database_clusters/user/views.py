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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms as horizon_forms
from horizon import tables as horizon_tables
from horizon.utils import memoized

from trove_dashboard import api
from trove_dashboard.content.database_clusters.user import forms
from trove_dashboard.content.database_clusters.user import tables
from trove_dashboard.content.databases import views as databases_views
from troveclient import exceptions as trove_exceptions


LOG = logging.getLogger(__name__)


class CreateUserView(horizon_forms.ModalFormView):
    form_class = forms.CreateUserForm
    form_id = "create_user_form"
    modal_header = _("Create User")
    modal_id = "create_user_modal"
    template_name = 'project/databases/create_user.html'
    submit_label = "Create User"
    submit_url = 'horizon:project:database_clusters:user:create_user'
    success_url = 'horizon:project:database_clusters:user:manage_users'

    def get_success_url(self):
        return reverse(self.success_url, args=(self.get_id(),))

    def get_context_data(self, **kwargs):
        context = super(CreateUserView, self).get_context_data(**kwargs)
        context['cluster_id'] = self.get_id()
        args = (self.get_id(),)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        cluster_id = self.get_id()
        cluster = self.get_cluster()
        return {'cluster_id': cluster_id,
                'datastore': cluster.datastore}

    @memoized.memoized_method
    def get_cluster(self):
        cluster_id = self.get_id()
        try:
            return api.trove.cluster_get(self.request, cluster_id)
        except Exception:
            msg = _('Unable to retrieve cluster details.')
            redirect = reverse(
                'horizon:project:database_clusters:user:manage_users',
                args=[cluster_id])
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_id(self):
        return self.kwargs['cluster_id']


class EditUserView(horizon_forms.ModalFormView):
    form_class = forms.EditUserForm
    form_id = "edit_user_form"
    modal_header = _("Edit User")
    modal_id = "edit_user_modal"
    template_name = 'project/databases/edit_user.html'
    submit_label = "Apply Changes"
    submit_url = 'horizon:project:database_clusters:user:edit_user'
    success_url = 'horizon:project:database_clusters:user:manage_users'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['cluster_id'],))

    def get_context_data(self, **kwargs):
        context = super(EditUserView, self).get_context_data(**kwargs)
        context['cluster_id'] = self.kwargs['cluster_id']
        context['user_name'] = self.kwargs['user_name']
        context['user_host'] = self.kwargs['user_host']
        args = (self.kwargs['cluster_id'], self.kwargs['user_name'],
                self.kwargs['user_host'])
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        cluster_id = self.kwargs['cluster_id']
        user_name = self.kwargs['user_name']
        user_host = self.kwargs['user_host']
        return {'cluster_id': cluster_id, 'user_name': user_name,
                'user_host': user_host}


class ManageUsersView(horizon_tables.DataTableView):
    table_class = tables.UsersTable
    template_name = 'project/database_clusters/user/users.html'
    page_title = _("Manage Users: {{ cluster.name }}")
    index_url = "horizon:project:database_clusters:user:manage_users"
    preload = False

    def get_context_data(self, **kwargs):
        context = super(ManageUsersView, self).get_context_data(**kwargs)
        context['cluster_id'] = self.kwargs['cluster_id']
        context['cluster'] = self.get_cluster(self.kwargs['cluster_id'])
        return context

    def get_data(self):
        try:
            cluster = self.get_cluster(self.kwargs['cluster_id'])
            users = self.get_users()
            for user in users:
                # user.cluster = cluster
                try:
                    user.access = self.get_user_list_access(self.request,
                                                            cluster.id,
                                                            user.name,
                                                            host=user.host)
                except exceptions.NOT_FOUND:
                    pass
                except trove_exceptions.BadRequest as e:
                    if not ("The 'list_access' operation "
                            "is not supported") in e.message:
                        raise
                    LOG.info("List user access is not available.  "
                             "Reason: %s", e.message)
                except Exception:
                    msg = _('Unable to get user access data.')
                    exceptions.handle(self.request, msg)
        except Exception:
            users = []
            msg = _('Unable to retrieve users list.')
            exceptions.handle(self.request, msg)
        return users

    @memoized.memoized_method
    def get_cluster(self, cluster_id):
        try:
            return api.trove.cluster_get(self.request, cluster_id)
        except Exception:
            redirect = reverse(self.index_url, args=[cluster_id])
            msg = _('Unable to retrieve cluster details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    @memoized.memoized_method
    def get_users(self):
        return api.trove.users_list(self.request, self.kwargs['cluster_id'])

    @memoized.memoized_method
    def get_user_list_access(self, request, cluster, name, host=None):
        return api.trove.user_list_access(request, cluster, name, host=host)


class AccessDetailView(horizon_tables.DataTableView):
    table_class = tables.AccessTable
    template_name = 'project/databases/access_detail.html'
    page_title = _("Database Access for: {{ user_name }}")
    index_url = 'horizon:project:database_clusters:user:manage_users'

    @memoized.memoized_method
    def get_data(self):
        cluster_id = self.kwargs['cluster_id']
        user_name = self.kwargs['user_name']
        user_host = self.kwargs['user_host']
        try:
            databases = api.trove.database_list(self.request, cluster_id)
        except Exception:
            databases = []
            redirect = reverse(self.index_url, args=[cluster_id])
            exceptions.handle(self.request,
                              _('Unable to retrieve databases.'),
                              redirect=redirect)
        try:
            granted = api.trove.user_show_access(
                self.request, cluster_id, user_name, host=user_host)
        except Exception:
            granted = []
            redirect = reverse(self.index_url, args=[cluster_id])
            exceptions.handle(self.request,
                              _('Unable to retrieve accessible databases.'),
                              redirect=redirect)

        db_access_list = []
        for database in databases:
            if database in granted:
                access = True
            else:
                access = False

            db_access = databases_views.DBAccess(database.name, access)
            db_access_list.append(db_access)

        return sorted(db_access_list, key=lambda data: (data.name))

    def get_context_data(self, **kwargs):
        context = super(AccessDetailView, self).get_context_data(**kwargs)
        context["db_access"] = self.get_data()
        return context
