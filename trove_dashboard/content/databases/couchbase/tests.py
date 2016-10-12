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

import six

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IsA  # noqa

from troveclient import common

from trove_dashboard import api
from trove_dashboard.test import helpers as test


class BucketTests(test.TestCase):
    BUCKETS_URL = reverse('horizon:project:databases:couchbase:manage_buckets',
                          args=['id'])
    CREATE_URL = reverse('horizon:project:databases:couchbase:create_bucket',
                         args=['id'])
    UPDATE_URL = reverse('horizon:project:databases:couchbase:update_bucket',
                         args=['id', 'id'])
    INDEX_TEMPLATE = 'project/databases/couchbase/buckets.html'

    @test.create_stubs({
        api.trove: ('bucket_list', 'instance_get')
    })
    def test_buckets(self):
        instance = self.databases.first()
        buckets = common.Paginated(self.trove_buckets.list())
        (api.trove.bucket_list(IsA(http.HttpRequest), IsA(six.text_type))
            .AndReturn(buckets))
        (api.trove.instance_get(IsA(http.HttpRequest), IsA(six.string_types))
            .AndReturn(instance))
        self.mox.ReplayAll()
        res = self.client.get(self.BUCKETS_URL)
        self.assertTemplateUsed(res, self.INDEX_TEMPLATE)

    @test.create_stubs({
        api.trove: ('bucket_list', 'instance_get',)
    })
    def test_buckets_exception(self):
        instance = self.databases.first()
        (api.trove.bucket_list(IsA(http.HttpRequest), IsA(six.text_type))
            .AndRaise(self.exceptions.trove))
        (api.trove.instance_get(IsA(http.HttpRequest), IsA(six.string_types))
            .AndReturn(instance))
        self.mox.ReplayAll()
        res = self.client.get(self.BUCKETS_URL)
        self.assertTemplateUsed(res, self.INDEX_TEMPLATE)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({
        api.trove: ('bucket_create',)
    })
    def test_create_new_bucket(self):
        new_bucket = {
            "name": "bucket1",
            "password": "password",
            "bucket_ramsize": 1024,
            "bucket_replica": 3,
            "enable_index_replica": False,
            "bucket_eviction_policy": "valueOnly",
            "bucket_priority": "low",
        }

        (api.trove.bucket_create(IsA(http.HttpRequest),
                                 IsA(six.text_type),
                                 IsA(six.text_type),
                                 IsA(six.text_type),
                                 bucket_ramsize=IsA(six.integer_types),
                                 bucket_replica=IsA(six.integer_types),
                                 enable_index_replica=True,
                                 bucket_eviction_policy=IsA(six.text_type),
                                 bucket_priority=IsA(six.text_type))
            .AndReturn(new_bucket))

        self.mox.ReplayAll()

        post = {
            'method': 'CreateBucketForm',
            'instance_id': 'id',
            'name': 'bucket1',
            'password': 'password',
            'bucket_ramsize': 1024,
            'bucket_replica': 3,
            'enable_index_replica': 0,
            'bucket_eviction_policy': 'valueOnly',
            'bucket_priority': 'low',
        }

        res = self.client.post(self.CREATE_URL, post)
        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({
        api.trove: ('bucket_create',)
    })
    def test_create_new_bucket_exception(self):
        (api.trove.bucket_create(IsA(http.HttpRequest),
                                 IsA(six.text_type),
                                 IsA(six.text_type),
                                 IsA(six.text_type),
                                 bucket_ramsize=IsA(six.integer_types),
                                 bucket_replica=IsA(six.integer_types),
                                 enable_index_replica=True,
                                 bucket_eviction_policy=IsA(six.text_type),
                                 bucket_priority=IsA(six.text_type))
            .AndRaise(self.exceptions.trove))

        self.mox.ReplayAll()

        post = {
            'method': 'CreateBucketForm',
            'instance_id': 'id',
            'name': 'bucket1',
            'password': 'password',
            'bucket_ramsize': 1024,
            'bucket_replica': 3,
            'enable_index_replica': 0,
            'bucket_eviction_policy': 'valueOnly',
            'bucket_priority': 'low',
        }

        res = self.client.post(self.CREATE_URL, post)
        self.assertEqual(res.status_code, 302)

    @test.create_stubs({
        api.trove: ('bucket_get', 'bucket_update',)
    })
    def test_update_bucket(self):
        buckets = common.Paginated(self.trove_buckets.list())
        updated_bucket = {
            "name": "bucket1",
            "password": "password",
            "bucket_ramsize": 1024,
            "bucket_replica": 3,
            'enable_index_replica': False,
            'bucket_eviction_policy': 'valueOnly',
            'bucket_priority': 'low',
        }

        (api.trove.bucket_get(IsA(http.HttpRequest),
                              IsA(six.text_type),
                              IsA(six.text_type))
            .AndReturn(buckets[0]))
        (api.trove.bucket_update(IsA(http.HttpRequest),
                                 IsA(six.text_type),
                                 IsA(six.text_type),
                                 new_password=IsA(six.text_type),
                                 bucket_ramsize=IsA(six.integer_types),
                                 bucket_replica=IsA(six.integer_types),
                                 enable_index_replica=True,
                                 bucket_eviction_policy=IsA(six.text_type),
                                 bucket_priority=IsA(six.text_type))
            .AndReturn(updated_bucket))

        self.mox.ReplayAll()

        post = {
            'method': 'CreateBucketForm',
            'instance_id': 'id',
            'name': 'bucket1',
            'password': 'password',
            'bucket_ramsize': 1024,
            'bucket_replica': 3,
            'enable_index_replica': 0,
            'bucket_eviction_policy': 'valueOnly',
            'bucket_priority': 'low',
        }

        res = self.client.post(self.UPDATE_URL, post)
        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({
        api.trove: ('bucket_get', 'bucket_update',)
    })
    def test_update_bucket_exception(self):
        buckets = common.Paginated(self.trove_buckets.list())
        (api.trove.bucket_get(IsA(http.HttpRequest),
                              IsA(six.text_type),
                              IsA(six.text_type))
            .AndReturn(buckets[0]))
        (api.trove.bucket_update(IsA(http.HttpRequest),
                                 IsA(six.text_type),
                                 IsA(six.text_type),
                                 new_password=IsA(six.text_type),
                                 bucket_ramsize=IsA(six.integer_types),
                                 bucket_replica=IsA(six.integer_types),
                                 enable_index_replica=True,
                                 bucket_eviction_policy=IsA(six.text_type),
                                 bucket_priority=IsA(six.text_type))
            .AndRaise(self.exceptions.trove))

        self.mox.ReplayAll()

        post = {
            'method': 'CreateBucketForm',
            'instance_id': 'id',
            'name': 'bucket1',
            'password': 'password',
            'bucket_ramsize': 1024,
            'bucket_replica': 3,
            'enable_index_replica': 0,
            'bucket_eviction_policy': 'valueOnly',
            'bucket_priority': 'low',
        }

        res = self.client.post(self.UPDATE_URL, post)
        self.assertEqual(res.status_code, 302)

    @test.create_stubs({
        api.trove: ('bucket_delete', 'bucket_list',)
    })
    def test_bucket_delete(self):
        buckets = common.Paginated(self.trove_buckets.list())
        (api.trove.bucket_delete(IsA(http.HttpRequest), IsA(six.text_type),
                                 IsA(six.text_type))
            .AndReturn(None))
        (api.trove.bucket_list(IsA(http.HttpRequest), IsA(six.text_type))
            .AndReturn(buckets))
        self.mox.ReplayAll()
        action_string = u"buckets__delete_bucket__%s" % buckets[0].name
        form_data = {'action': action_string}
        res = self.client.post(self.BUCKETS_URL, form_data)
        self.assertRedirectsNoFollow(res, self.BUCKETS_URL)
