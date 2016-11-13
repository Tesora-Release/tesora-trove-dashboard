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

from trove_dashboard import api
from trove_dashboard.test import helpers as test

INDEX_URL = reverse(
    'horizon:project:database_clusters:database:manage_databases', args=['id'])


class DatabaseTests(test.TestCase):
    @test.create_stubs({
        api.trove: ('cluster_get', 'database_list',)
    })
    def test_manage_database_view(self):
        cluster = self.trove_clusters.first()
        databases = self.databases.list()

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(cluster))
        (api.trove.database_list(IsA(http.HttpRequest),
                                 IsA(six.text_type))
            .AndReturn(databases))
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(
            res, 'project/database_clusters/database/databases.html')

    @test.create_stubs({
        api.trove: ('cluster_get', 'database_list',)
    })
    def test_manage_database_view_database_list_exception(self):
        cluster = self.trove_clusters.first()

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(cluster))
        (api.trove.database_list(IsA(http.HttpRequest),
                                 IsA(six.text_type))
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(
            res, 'project/database_clusters/database/databases.html')
        self.assertMessageCount(res, error=1)

    @test.create_stubs({
        api.trove: ('cluster_get',)
    })
    def test_create_database(self):
        cluster = self.trove_clusters.first()

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(cluster))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:'
                      'database:create_database',
                      args=['id'])
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'project/databases/create_database.html')

    @test.create_stubs({
        api.trove: ('database_create', 'cluster_get',)
    })
    def test_create_new_database(self):
        database = self.databases.first()
        new_database = {
            "status": "ACTIVE",
            "updated": "2013-08-12T22:00:09",
            "name": "NewDB",
            "links": [],
            "created": "2013-08-12T22:00:03",
            "ip": [
                "10.0.0.3",
            ],
            "volume": {
                "used": 0.13,
                "size": 1,
            },
            "flavor": {
                "id": "1",
                "links": [],
            },
            "datastore": {
                "type": "mysql",
                "version": "5.5"
            },
            "id": "12345678-73db-4e23-b52e-368937d72719",
        }

        (api.trove.database_create(IsA(http.HttpRequest),
                                   IsA(six.text_type),
                                   IsA(six.text_type),
                                   character_set=IsA(six.text_type),
                                   collation=IsA(six.text_type))
            .AndReturn(new_database))
        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(database))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:'
                      'database:create_database',
                      args=['id'])
        post = {
            'method': 'CreateDatabaseForm',
            'cluster_id': 'id',
            'name': 'NewDB'}

        res = self.client.post(url, post)
        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.trove: ('database_create', 'cluster_get')})
    def test_create_new_database_exception(self):
        database = self.databases.first()

        (api.trove.database_create(IsA(http.HttpRequest),
                                   IsA(six.text_type),
                                   IsA(six.text_type),
                                   character_set=IsA(six.text_type),
                                   collation=IsA(six.text_type))
            .AndRaise(self.exceptions.trove))
        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(database))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:'
                      'database:create_database',
                      args=['id'])
        post = {
            'method': 'CreateDatabaseForm',
            'cluster_id': 'id',
            'name': 'NewDB'}

        res = self.client.post(url, post)
        self.assertEqual(res.status_code, 302)

    @test.create_stubs({
        api.trove: ('cluster_get',)
    })
    def test_create_new_database_optional_fields_mysql(self):
        database = self.databases.first()

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(database))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:'
                      'database:create_database',
                      args=['id'])
        res = self.client.get(url)
        character_set_field = res.context_data['form'].fields['character_set']
        collation_field = res.context_data['form'].fields['collation']
        self.assertFalse(character_set_field.widget.is_hidden)
        self.assertFalse(collation_field.widget.is_hidden)

    @test.create_stubs({
        api.trove: ('cluster_get',)
    })
    def test_create_new_database_optional_fields_not_mysql(self):
        database = self.databases.list()[3]

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(database))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:'
                      'database:create_database',
                      args=['id'])
        res = self.client.get(url)
        character_set_field = res.context_data['form'].fields['character_set']
        collation_field = res.context_data['form'].fields['collation']
        self.assertTrue(character_set_field.widget.is_hidden)
        self.assertTrue(collation_field.widget.is_hidden)
