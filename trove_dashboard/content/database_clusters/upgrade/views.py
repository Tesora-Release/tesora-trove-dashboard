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
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms as horizon_forms

from horizon.utils import memoized

from trove_dashboard import api
from trove_dashboard.content.database_clusters.upgrade import forms


class UpgradeClusterView(horizon_forms.ModalFormView):
    form_class = forms.UpgradeClusterForm
    form_id = "upgrade_cluster_form"
    modal_header = _("Upgrade Cluster")
    modal_id = "upgrade_cluster_modal"
    template_name = "project/database_clusters/upgrade/upgrade_cluster.html"
    submit_url = 'horizon:project:database_clusters:upgrade:upgrade_cluster'
    success_url = reverse_lazy('horizon:project:database_clusters:index')

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        cluster_id = self.kwargs['cluster_id']

        try:
            return api.trove.cluster_get(self.request, cluster_id)
        except Exception:
            redirect = reverse('horizon:project:database_clusters:index')
            msg = _('Unable to retrieve cluster details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpgradeClusterView, self).get_context_data(**kwargs)
        context['cluster_id'] = self.kwargs['cluster_id']
        args = (self.kwargs['cluster_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def get_datastore_versions(self, datastore, *args, **kwargs):
        try:
            return api.trove.datastore_version_list(self.request, datastore)
        except Exception:
            redirect = reverse("horizon:project:database_clusters:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve datastore versions.'),
                              redirect=redirect)

    def get_initial(self):
        initial = super(UpgradeClusterView, self).get_initial()
        obj = self.get_object()
        if obj:
            initial.update({'cluster_id': self.kwargs['cluster_id'],
                            'cluster_name': obj.name,
                            'old_version_name': obj.datastore['version'],
                            'datastore_versions': self.get_datastore_versions(
                                obj.datastore['type'])})
        return initial
