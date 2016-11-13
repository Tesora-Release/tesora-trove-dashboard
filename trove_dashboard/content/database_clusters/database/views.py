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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms as horizon_forms
from horizon import tables as horizon_tables
from horizon.utils import memoized

from trove_dashboard import api
from trove_dashboard.content.database_clusters.database import forms
from trove_dashboard.content.database_clusters.database import tables


class CreateDatabaseView(horizon_forms.ModalFormView):
    form_class = forms.CreateDatabaseForm
    form_id = "create_database_form"
    modal_header = _("Create Database")
    modal_id = "create_database_modal"
    template_name = 'project/databases/create_database.html'
    submit_label = "Create Database"
    submit_url = 'horizon:project:database_clusters:database:create_database'
    success_url = 'horizon:project:database_clusters:database:manage_databases'

    def get_success_url(self):
        return reverse(self.success_url, args=(self.get_id(),))

    def get_context_data(self, **kwargs):
        context = super(CreateDatabaseView, self).get_context_data(**kwargs)
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
                'horizon:project:database_clusters:database:manage_databases',
                args=[cluster_id])
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_id(self):
        return self.kwargs['cluster_id']


class ManageDatabasesView(horizon_tables.DataTableView):
    table_class = tables.DatabasesTable
    template_name = 'project/database_clusters/database/databases.html'
    page_title = _("Manage Databases: {{ cluster.name }}")
    index_url = "horizon:project:database_clusters:database:manage_databases"
    preload = False

    def get_context_data(self, **kwargs):
        context = super(ManageDatabasesView, self).get_context_data(**kwargs)
        context['cluster_id'] = self.kwargs['cluster_id']
        context['cluster'] = self.get_cluster(self.kwargs['cluster_id'])
        return context

    def get_data(self):
        try:
            databases = self.get_databases()
        except Exception:
            databases = []
            msg = _('Unable to retrieve databases list.')
            exceptions.handle(self.request, msg)
        return databases

    @memoized.memoized_method
    def get_cluster(self, cluster_id):
        try:
            return api.trove.cluster_get(self.request, cluster_id)
        except Exception:
            redirect = reverse(self.index_url)
            msg = _('Unable to retrieve cluster details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    @memoized.memoized_method
    def get_databases(self):
        return api.trove.database_list(self.request, self.kwargs['cluster_id'])
