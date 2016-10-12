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
from trove_dashboard.content.databases.couchbase import forms
from trove_dashboard.content.databases.couchbase import tables


class ManageBucketsView(horizon_tables.DataTableView):
    table_class = tables.BucketsTable
    template_name = 'project/databases/couchbase/buckets.html'
    page_title = _("Manage Buckets: {{ instance.name }}")
    index_url = "horizon:project:databases:index"
    preload = False

    def get_context_data(self, **kwargs):
        context = super(ManageBucketsView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        context['instance'] = self.get_instance(self.kwargs['instance_id'])
        return context

    def get_data(self):
        try:
            buckets = self.get_buckets()
        except Exception:
            buckets = []
            msg = _('Unable to retrieve buckets list.')
            exceptions.handle(self.request, msg)
        return buckets

    @memoized.memoized_method
    def get_instance(self, instance_id):
        try:
            return api.trove.instance_get(self.request, instance_id)
        except Exception:
            redirect = reverse(self.index_url)
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    @memoized.memoized_method
    def get_buckets(self):
        return api.trove.bucket_list(self.request, self.kwargs['instance_id'])


class CreateBucketView(horizon_forms.ModalFormView):
    form_class = forms.CreateBucketForm
    form_id = "create_bucket_form"
    modal_header = _("Create Bucket")
    modal_id = "create_bucket_modal"
    template_name = 'project/databases/couchbase/create_bucket.html'
    submit_label = _("Create Bucket")
    submit_url = 'horizon:project:databases:couchbase:create_bucket'
    success_url = 'horizon:project:databases:couchbase:manage_buckets'
    page_title = _("Create Bucket")

    def get_context_data(self, **kwargs):
        context = (super(CreateBucketView, self).get_context_data(**kwargs))
        context['instance_id'] = self.kwargs['instance_id']
        args = (self.kwargs['instance_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        initial = super(CreateBucketView, self).get_initial()
        initial['instance_id'] = self.kwargs['instance_id']
        return initial

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['instance_id'],))


class UpdateBucketView(horizon_forms.ModalFormView):
    form_class = forms.UpdateBucketForm
    form_id = "update_bucket_form"
    modal_header = _("Update Bucket")
    modal_id = "update_bucket_modal"
    template_name = 'project/databases/couchbase/update_bucket.html'
    submit_label = _("Update Bucket")
    submit_url = 'horizon:project:databases:couchbase:update_bucket'
    success_url = 'horizon:project:databases:couchbase:manage_buckets'
    page_title = _("Update Bucket")

    def get_context_data(self, **kwargs):
        context = (super(UpdateBucketView, self).get_context_data(**kwargs))
        context['instance_id'] = self.kwargs['instance_id']
        context['bucket_id'] = self.kwargs['bucket_id']
        args = (self.kwargs['instance_id'], self.kwargs['bucket_id'])
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        initial = super(UpdateBucketView, self).get_initial()
        initial['instance_id'] = self.kwargs['instance_id']
        initial['bucket_id'] = self.kwargs['bucket_id']
        return initial

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['instance_id'],))
