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
from django import http

from mox3.mox import IsA  # noqa
import six

from troveclient import common

from trove_dashboard import api
from trove_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:project:database_topology:index')
REPLICAS_URL = reverse('horizon:project:database_topology:replicas',
                       args=['id'])


class DatabaseTopologyTests(test.TestCase):
    @test.create_stubs({
        api.trove: ('flavor_list', 'instance_list_master',)
    })
    def test_index(self):
        databases = common.Paginated(self.databases.list())
        (api.trove.instance_list_master(IsA(http.HttpRequest), marker=None)
            .AndReturn(databases))
        (api.trove.flavor_list(IsA(http.HttpRequest))
            .AndReturn(self.flavors.list()))
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/database_topology/index.html')

    @test.create_stubs({
        api.trove: ('flavor_list', 'instance_list_master',)
    })
    def test_index_pagination(self):
        databases = self.databases.list()
        last_record = databases[-1]
        databases = common.Paginated(databases, next_marker="foo")
        (api.trove.instance_list_master(IsA(http.HttpRequest), marker=None)
            .AndReturn(databases))
        (api.trove.flavor_list(IsA(http.HttpRequest))
            .AndReturn(self.flavors.list()))
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/database_topology/index.html')
        self.assertContains(
            res, 'marker=' + last_record.id)

    @test.create_stubs({
        api.trove: ('instance_list_master',)
    })
    def test_index_list_exception(self):
        (api.trove.instance_list_master(IsA(http.HttpRequest), marker=None)
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/database_topology/index.html')
        self.assertMessageCount(res, error=1)

    @test.create_stubs({
        api.trove: ('flavor_list', 'instance_list_master',)
    })
    def test_index_flavor_exception(self):
        databases = common.Paginated(self.databases.list())
        (api.trove.instance_list_master(IsA(http.HttpRequest), marker=None)
            .AndReturn(databases))
        (api.trove.flavor_list(IsA(http.HttpRequest))
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/database_topology/index.html')
        self.assertMessageCount(res, error=1)

    @test.create_stubs({
        api.trove: ('flavor_list', 'instance_get',)
    })
    def test_replicas(self):
        master = self.databases.list()[2]
        (api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))
            .AndReturn(master))
        (api.trove.instance_get(IsA(http.HttpRequest), IsA(six.string_types))
            .AndReturn(self.databases.first()))
        (api.trove.flavor_list(IsA(http.HttpRequest))
            .AndReturn(self.flavors.list()))
        self.mox.ReplayAll()

        res = self.client.get(REPLICAS_URL)
        self.assertTemplateUsed(res, 'project/database_topology/replica.html')

    @test.create_stubs({
        api.trove: ('instance_get',)
    })
    def test_replicas_instance_get_exception(self):
        (api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()
        res = self.client.get(REPLICAS_URL)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({
        api.trove: ('flavor_list', 'instance_get',)
    })
    def test_replicas_flavor_exception(self):
        master = self.databases.list()[2]
        (api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))
            .AndReturn(master))
        (api.trove.instance_get(IsA(http.HttpRequest), IsA(six.string_types))
            .AndReturn(self.databases.first()))
        (api.trove.flavor_list(IsA(http.HttpRequest))
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()

        res = self.client.get(REPLICAS_URL)
        self.assertTemplateUsed(res, 'project/database_topology/replica.html')
