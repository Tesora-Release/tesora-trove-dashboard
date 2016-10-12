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

from trove_dashboard import api
from trove_dashboard.content.databases.couchbase import (
    tests as database_couchbase_tests)
from trove_dashboard.test import helpers as test


class BucketTests(database_couchbase_tests.BucketTests):
    BUCKETS_URL = reverse(
        'horizon:project:database_clusters:couchbase:manage_buckets',
        args=['id'])
    CREATE_URL = reverse(
        'horizon:project:database_clusters:couchbase:create_bucket',
        args=['id'])
    UPDATE_URL = reverse(
        'horizon:project:database_clusters:couchbase:update_bucket',
        args=['id', 'id'])

    @test.create_stubs({
        api.trove: ('bucket_delete', 'bucket_list',)
    })
    def test_bucket_delete(self):
        pass
