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
from trove_dashboard.content.databases import db_capability
from trove_dashboard.content import utils as database_utils


class ManageBuckets(tables.LinkAction):
    name = "manage_buckets"
    verbose_name = _("Manage Buckets")
    url = "horizon:project:databases:couchbase:manage_buckets"

    def allowed(self, request, instance=None):
        return (instance.status in database_utils.ACTIVE_STATES and
                db_capability.is_couchbase_datastore(
                    instance.datastore['type']))

    def get_link_url(self, datum):
        return urlresolvers.reverse(self.url, args=[datum.id])


class CreateBucket(tables.LinkAction):
    name = "create_bucket"
    verbose_name = _("Create Bucket")
    url = "horizon:project:databases:couchbase:create_bucket"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum=None):
        instance_id = self.table.kwargs['instance_id']
        return urlresolvers.reverse(self.url, args=[instance_id])


class UpdateBucket(tables.LinkAction):
    name = "update_bucket"
    verbose_name = _("Update Bucket")
    url = "horizon:project:databases:couchbase:update_bucket"
    classes = ("ajax-modal",)

    def get_link_url(self, datum):
        instance_id = self.table.kwargs['instance_id']
        bucket_id = self.table.get_object_id(datum)
        return urlresolvers.reverse(self.url, args=[instance_id, bucket_id])


class DeleteBucket(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Bucket",
            u"Delete Buckets",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Bucket",
            u"Deleted Buckets",
            count
        )

    name = "delete_bucket"

    def delete(self, request, obj_id):
        instance_id = self.table.kwargs['instance_id']
        api.trove.bucket_delete(request, instance_id, obj_id)


class BucketsTable(tables.DataTable):
    name = tables.Column(
        'name',
        verbose_name=_('Name'))
    bucket_ramsize = tables.Column(
        'bucket_ramsize',
        verbose_name=_('Bucket RAM Size'))
    bucket_replica = tables.Column(
        'bucket_replica',
        verbose_name=_('Bucket Replica Count'))
    used_ram = tables.Column(
        'used_ram',
        verbose_name=_('RAM Used (MB)'))

    class Meta(object):
        name = "buckets"
        verbose_name = _("Buckets")
        table_actions = (CreateBucket,)
        row_actions = (UpdateBucket, DeleteBucket)

    def get_object_id(self, datum):
        return datum.name
