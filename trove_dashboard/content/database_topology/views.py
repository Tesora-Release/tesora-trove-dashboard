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
from horizon.utils import memoized

from trove_dashboard import api
from trove_dashboard.content.database_topology import tables
from trove_dashboard.content.databases import views as database_views


class IndexView(database_views.IndexView):
    table_class = tables.MastersTable
    template_name = 'project/database_topology/index.html'
    page_title = _("Master Instances")

    @memoized.memoized_method
    def get_data(self):
        try:
            marker = self.request.GET.get(
                tables.MastersTable._meta.pagination_param)
            instances = api.trove.instance_list_master(self.request,
                                                       marker=marker)
            self._more = instances.next or False
        except Exception:
            self._more = False
            instances = []
            msg = _('Error getting master instances list.')
            exceptions.handle(self.request, msg)
        map(self._extra_data, instances)
        return instances


class ViewReplicas(database_views.IndexView):
    table_class = tables.ReplicasTable
    template_name = 'project/database_topology/replica.html'
    page_title = _("Replicas of: {{ master }}")

    _more = False

    def get_context_data(self, **kwargs):
        context = super(ViewReplicas, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        if hasattr(self, 'instance'):
            context['master'] = self.instance.name
        return context

    @memoized.memoized_method
    def get_data(self):
        instance_id = self.kwargs['instance_id']
        try:
            self.instance = api.trove.instance_get(self.request, instance_id)
        except Exception:
            redirect = reverse('horizon:project:database_topology:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve instance details.'),
                              redirect=redirect)
        replicas = []
        try:
            if hasattr(self.instance, 'replicas'):
                for replica in self.instance.replicas:
                    replicas.append(api.trove.instance_get(self.request,
                                                           replica['id']))
            map(self._extra_data, replicas)
        except Exception:
            replicas = []
            redirect = reverse('horizon:project:database_topology:index')
            exceptions.handle(self.request,
                              _('Unable to obtain replica list.'),
                              redirect=redirect)
        return replicas
