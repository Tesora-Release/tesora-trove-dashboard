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

from trove_dashboard.content.database_clusters.couchbase import forms
from trove_dashboard.content.database_clusters.couchbase import tables
from trove_dashboard.content.databases.couchbase import (
    views as databases_couchbase_views)


class ManageBucketsView(databases_couchbase_views.ManageBucketsView):
    table_class = tables.BucketsTable
    index_url = "horizon:project:database_clusters:couchbase:manage_buckets"


class CreateBucketView(databases_couchbase_views.CreateBucketView):
    form_class = forms.CreateBucketForm
    submit_url = 'horizon:project:database_clusters:couchbase:create_bucket'
    success_url = 'horizon:project:database_clusters:couchbase:manage_buckets'


class UpdateBucketView(databases_couchbase_views.UpdateBucketView):
    form_class = forms.UpdateBucketForm
    submit_url = 'horizon:project:database_clusters:couchbase:update_bucket'
    success_url = 'horizon:project:database_clusters:couchbase:manage_buckets'
