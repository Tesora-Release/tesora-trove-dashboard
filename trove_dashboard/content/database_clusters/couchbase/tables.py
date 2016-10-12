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

from trove_dashboard.content.databases.couchbase import (
    tables as databases_couchbase_tables)


class ManageBuckets(databases_couchbase_tables.ManageBuckets):
    url = "horizon:project:database_clusters:couchbase:manage_buckets"


class CreateBucket(databases_couchbase_tables.CreateBucket):
    url = "horizon:project:database_clusters:couchbase:create_bucket"


class UpdateBucket(databases_couchbase_tables.UpdateBucket):
    url = "horizon:project:database_clusters:couchbase:update_bucket"


class BucketsTable(databases_couchbase_tables.BucketsTable):
    class Meta(object):
        table_actions = (CreateBucket,)
        row_actions = (UpdateBucket, databases_couchbase_tables.DeleteBucket)
