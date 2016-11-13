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
from horizon import forms
from horizon import messages

from trove_dashboard import api


class CreateBucketForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(
        label=_("Name"))
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(),
        min_length=6,
        max_length=24)
    bucket_ramsize = forms.IntegerField(
        label=_("Bucket RAM Size"),
        min_value=100,
        help_text=_("Optional bucket RAM quota in MB."))
    bucket_replica = forms.IntegerField(
        label=_("Bucket Replica Count"),
        min_value=0,
        max_value=3,
        help_text=_("Optional replication count."))
    enable_index_replica = forms.BooleanField(
        label=_("Enable Index Replica"),
        required=False,
        widget=forms.CheckboxInput(),
        help_text=_("Optionally enable or disable index replicas."))
    bucket_eviction_policy = forms.ChoiceField(
        label=_("Bucket Eviction Policy"),
        help_text=_("Optionally define the eviction policy."),
        choices=[
            ('valueOnly', 'valueOnly'),
            ('fullEviction', 'fullEviction')])
    bucket_priority = forms.ChoiceField(
        label=_("Bucket Priority"),
        help_text=_("Optional bucket priority compared to other buckets."),
        choices=[
            ('low', 'low'),
            ('high', 'high')])
    index_url = "horizon:project:databases:couchbase:manage_buckets"

    def _get_bucket_ramsize(self, data):
        bucket_ramsize = None
        if data["bucket_ramsize"]:
            bucket_ramsize = data["bucket_ramsize"]
        return bucket_ramsize

    def _get_bucket_replica(self, data):
        bucket_replica = None
        if data["bucket_replica"]:
            bucket_replica = data["bucket_replica"]
        return bucket_replica

    def _get_bucket_eviction_policy(self, data):
        bucket_eviction_policy = None
        if data["bucket_eviction_policy"]:
            bucket_eviction_policy = data["bucket_eviction_policy"]
        return bucket_eviction_policy

    def _get_bucket_priority(self, data):
        bucket_priority = None
        if data["bucket_priority"]:
            bucket_priority = data["bucket_priority"]
        return bucket_priority

    def handle(self, request, data):
        instance = data.get('instance_id')
        try:
            api.trove.bucket_create(
                request,
                instance,
                data["name"],
                data["password"],
                bucket_ramsize=self._get_bucket_ramsize(data),
                bucket_replica=self._get_bucket_replica(data),
                enable_index_replica=data["enable_index_replica"],
                bucket_eviction_policy=(self._get_bucket_eviction_policy(
                                        data)),
                bucket_priority=self._get_bucket_priority(data))
            messages.success(
                request, _('Creating Bucket "%s"') % data.get('name'))
        except Exception as e:
            args = (instance,)
            redirect = reverse(self.index_url, args=args)
            exceptions.handle(request,
                              _('Unable to create bucket. %s') %
                              e.message, redirect=redirect)
        return True


class UpdateBucketForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(
        label=_("Name"),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(),
        min_length=6,
        max_length=24)
    bucket_ramsize = forms.IntegerField(
        label=_("Bucket RAM Size"),
        min_value=100,
        help_text=_("Optional bucket RAM quota in MB."))
    bucket_replica = forms.IntegerField(
        label=_("Bucket Replica Count"),
        min_value=0,
        max_value=3,
        help_text=_("Optional replication count."))
    enable_index_replica = forms.BooleanField(
        label=_("Enable Index Replica"),
        required=False,
        widget=forms.CheckboxInput(),
        help_text=_("Optionally enable or disable index replicas."))
    bucket_eviction_policy = forms.ChoiceField(
        label=_("Bucket Eviction Policy"),
        help_text=_("Optionally define the eviction policy."),
        choices=[
            ('valueOnly', 'valueOnly'),
            ('fullEviction', 'fullEviction')])
    bucket_priority = forms.ChoiceField(
        label=_("Bucket Priority"),
        help_text=_("Optional bucket priority compared to other buckets."),
        choices=[
            ('low', 'low'),
            ('high', 'high')])
    index_url = "horizon:project:databases:couchbase:manage_buckets"

    def __init__(self, request, *args, **kwargs):
        super(UpdateBucketForm, self).__init__(request, *args, **kwargs)

        instance_id = (kwargs.get('initial', {}).get('instance_id'))
        bucket_id = (kwargs.get('initial', {}).get('bucket_id'))

        bucket = api.trove.bucket_get(request, instance_id, bucket_id)
        if bucket:
            self.fields['name'].initial = bucket.name
            self.fields['bucket_ramsize'].initial = bucket.bucket_ramsize
            self.fields['bucket_replica'].initial = bucket.bucket_replica

    def _get_password(self, data):
        password = None
        if data["password"]:
            password = data["password"]
        return password

    def _get_bucket_ramsize(self, data):
        bucket_ramsize = None
        if data["bucket_ramsize"]:
            bucket_ramsize = data["bucket_ramsize"]
        return bucket_ramsize

    def _get_bucket_replica(self, data):
        bucket_replica = None
        if data["bucket_replica"]:
            bucket_replica = data["bucket_replica"]
        return bucket_replica

    def _get_bucket_eviction_policy(self, data):
        bucket_eviction_policy = None
        if data["bucket_eviction_policy"]:
            bucket_eviction_policy = data["bucket_eviction_policy"]
        return bucket_eviction_policy

    def _get_bucket_priority(self, data):
        bucket_priority = None
        if data["bucket_priority"]:
            bucket_priority = data["bucket_priority"]
        return bucket_priority

    def handle(self, request, data):
        instance = data.get('instance_id')
        try:
            api.trove.bucket_update(
                request,
                instance,
                data["name"],
                new_password=self._get_password(data),
                bucket_ramsize=self._get_bucket_ramsize(data),
                bucket_replica=self._get_bucket_replica(data),
                enable_index_replica=data["enable_index_replica"],
                bucket_eviction_policy=(self._get_bucket_eviction_policy(
                                        data)),
                bucket_priority=self._get_bucket_priority(data))
            messages.success(
                request, _('Updated Bucket "%s"') % data.get('name'))
        except Exception as e:
            args = (instance,)
            redirect = reverse(self.index_url, args=args)
            exceptions.handle(request,
                              _('Unable to update bucket. %s') %
                              e.message, redirect=redirect)
        return True
