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
from trove_dashboard.content.database_clusters.user import forms
from trove_dashboard.content.database_clusters.user import tables
from trove_dashboard.content.databases import views as databases_views
from trove_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:project:database_clusters:user:manage_users',
                    args=['id'])


class UserTests(test.TestCase):
    @test.create_stubs({
        api.trove: ('cluster_get', 'user_list_access', 'users_list',)
    })
    def test_manage_user_view(self):
        cluster = self.trove_clusters.first()
        users = self.database_users.list()
        user_db = self.database_user_dbs.first()

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(cluster))
        (api.trove.user_list_access(IsA(http.HttpRequest),
                                    IsA(str),
                                    IsA(str),
                                    host=IsA(str)).AndReturn([user_db]))
        (api.trove.users_list(IsA(http.HttpRequest),
                              IsA(six.string_types))
            .AndReturn(users))
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res,
                                'project/database_clusters/user/users.html')

    @test.create_stubs({
        api.trove: ('cluster_get', 'users_list',)
    })
    def test_manage_user_view_user_list_exception(self):
        cluster = self.trove_clusters.first()

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(cluster))
        (api.trove.users_list(IsA(http.HttpRequest),
                              IsA(six.string_types))
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res,
                                'project/database_clusters/user/users.html')
        self.assertMessageCount(res, error=1)

    @test.create_stubs({
        api.trove: ('cluster_get',)
    })
    def test_create_user(self):
        cluster = self.trove_clusters.first()

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(cluster))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:user:create_user',
                      args=[cluster.id])
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'project/databases/create_user.html')

    @test.create_stubs({
        api.trove: ('cluster_get', 'user_create',)
    })
    def test_create_new_user(self):
        cluster = self.trove_clusters.first()
        new_user = {
            "name": "Test_User2",
            "host": "%",
            "databases": ["TestDB"],
            "roles": []
        }

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(cluster))
        (api.trove.user_create(IsA(http.HttpRequest),
                               IsA(six.text_type),
                               IsA(six.text_type),
                               IsA(six.text_type),
                               host=IsA(six.text_type),
                               databases=[],
                               roles=None)
            .AndReturn(new_user))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:user:create_user',
                      args=[cluster.id])
        post = {
            'method': 'CreateUserForm',
            'cluster_id': cluster.id,
            'name': cluster.name,
            'password': 'password'}
        res = self.client.post(url, post)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({
        api.trove: ('cluster_get', 'user_create',)
    })
    def test_create_new_user_exception(self):
        cluster = self.trove_clusters.first()

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(cluster))
        (api.trove.user_create(IsA(http.HttpRequest),
                               IsA(six.text_type),
                               IsA(six.text_type),
                               IsA(six.text_type),
                               host=IsA(six.text_type),
                               databases=[],
                               roles=None)
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:user:create_user',
                      args=[cluster.id])
        post = {
            'method': 'CreateUserForm',
            'cluster_id': cluster.id,
            'name': cluster.name,
            'password': 'password'}
        res = self.client.post(url, post)

        self.assertEqual(res.status_code, 302)

    @test.create_stubs({
        api.trove: ('user_update_attributes',)
    })
    def test_edit_user(self):
        cluster = self.trove_clusters.first()
        user = self.users.first()

        (api.trove.user_update_attributes(IsA(http.HttpRequest),
                                          IsA(six.text_type),
                                          IsA(six.text_type),
                                          host=IsA(six.text_type),
                                          new_name=IsA(six.text_type),
                                          new_password=IsA(six.text_type),
                                          new_host=IsA(six.text_type)))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:user:edit_user',
                      args=[cluster.id, user.name, '%'])
        post = {
            'method': 'EditUserForm',
            'cluster_id': cluster.id,
            'user_name': user.name,
            'user_host': '%',
            'new_name': 'new_name',
            'new_password': 'new_password',
            'new_host': '127.0.0.1'}

        res = self.client.post(url, post)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({
        api.trove: ('user_update_attributes',)
    })
    def test_edit_user_exception(self):
        cluster = self.trove_clusters.first()
        user = self.users.first()

        (api.trove.user_update_attributes(IsA(http.HttpRequest),
                                          IsA(six.text_type),
                                          IsA(six.text_type),
                                          host=IsA(six.text_type),
                                          new_name=IsA(six.text_type),
                                          new_password=IsA(six.text_type),
                                          new_host=IsA(six.text_type))
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:user:edit_user',
                      args=[cluster.id, user.name, '%'])
        post = {
            'method': 'EditUserForm',
            'cluster_id': cluster.id,
            'user_name': user.name,
            'user_host': '%',
            'new_name': 'new_name',
            'new_password': 'new_password',
            'new_host': '127.0.0.1'}
        res = self.client.post(url, post)

        self.assertEqual(res.status_code, 302)

    def test_edit_user_no_values(self):
        cluster = self.trove_clusters.first()
        user = self.users.first()

        url = reverse('horizon:project:database_clusters:user:edit_user',
                      args=[cluster.id, user.name, '%'])
        post = {
            'method': 'EditUserForm',
            'cluster_id': cluster.id,
            'user_name': user.name,
            'user_host': '%',
        }
        res = self.client.post(url, post)

        msg = forms.EditUserForm.validation_error_message
        self.assertFormError(res, "form", None, [msg])

    @test.create_stubs({
        api.trove: ('database_list', 'user_show_access',)
    })
    def test_access_get(self):
        cluster = self.trove_clusters.first()
        user = self.users.first()

        (api.trove.database_list(IsA(http.HttpRequest),
                                 IsA(six.text_type))
            .AndReturn(self.databases.list()))
        (api.trove.user_show_access(IsA(http.HttpRequest),
                                    IsA(six.text_type),
                                    IsA(six.text_type),
                                    host=IsA(six.text_type))
            .AndReturn(self.databases.list()))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:user:access_detail',
                      args=[cluster.id, user.name, '%'])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/databases/access_detail.html')

    @test.create_stubs({
        api.trove: ('database_list', 'user_show_access',)
    })
    def test_access_get_exception(self):
        user = self.users.first()

        (api.trove.database_list(IsA(http.HttpRequest),
                                 IsA(six.text_type))
            .AndReturn(self.databases.list()))
        (api.trove.user_show_access(IsA(http.HttpRequest),
                                    IsA(six.text_type),
                                    IsA(six.text_type),
                                    host=IsA(six.text_type))
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:user:access_detail',
                      args=['id', user.name, '%'])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({
        api.trove: ('user_grant_access',)
    })
    def test_grant_access(self):
        (api.trove.user_grant_access(IsA(http.HttpRequest),
                                     IsA(six.text_type),
                                     IsA(six.text_type),
                                     [IsA(six.text_type)],
                                     host=IsA(six.text_type)))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:user:access_detail',
                      args=['id', 'name', 'host'])
        form_data = {"action": "access__grant_access__%s" % 'db1'}
        req = self.factory.post(url, form_data)

        kwargs = {'cluster_id': 'id', 'user_name': 'name', 'user_host': '%'}

        db_access_list = []
        db_access = databases_views.DBAccess('db1', False)
        db_access_list.append(db_access)

        table = tables.AccessTable(req, db_access_list, **kwargs)
        handled = table.maybe_handle()

        handled_url = handled['location']
        self.assertEqual(handled_url, url)

    @test.create_stubs({
        api.trove: ('user_grant_access',)
    })
    def test_grant_access_exception(self):
        (api.trove.user_grant_access(IsA(http.HttpRequest),
                                     IsA(six.text_type),
                                     IsA(six.text_type),
                                     [IsA(six.text_type)],
                                     host=IsA(six.text_type))
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:user:access_detail',
                      args=['id', 'name', 'host'])
        form_data = {"action": "access__grant_access__%s" % 'db1'}
        req = self.factory.post(url, form_data)

        kwargs = {'cluster_id': 'id', 'user_name': 'name', 'user_host': '%'}

        db_access_list = []
        db_access = databases_views.DBAccess('db1', False)
        db_access_list.append(db_access)

        table = tables.AccessTable(req, db_access_list, **kwargs)
        handled = table.maybe_handle()

        handled_url = handled['location']
        self.assertEqual(handled_url, url)

    @test.create_stubs({
        api.trove: ('user_revoke_access',)
    })
    def test_revoke_access(self):
        (api.trove.user_revoke_access(IsA(http.HttpRequest),
                                      IsA(six.text_type),
                                      IsA(six.text_type),
                                      [IsA(six.text_type)],
                                      host=IsA(six.text_type)))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:user:access_detail',
                      args=['id', 'name', 'host'])
        form_data = {"action": "access__revoke_access__%s" % 'db1'}
        req = self.factory.post(url, form_data)

        kwargs = {'cluster_id': 'id', 'user_name': 'name', 'user_host': '%'}

        db_access_list = []
        db_access = databases_views.DBAccess('db1', True)
        db_access_list.append(db_access)

        table = tables.AccessTable(req, db_access_list, **kwargs)
        handled = table.maybe_handle()

        handled_url = handled['location']
        self.assertEqual(handled_url, url)

    @test.create_stubs({
        api.trove: ('user_revoke_access',)
    })
    def test_detail_revoke_access_exception(self):
        (api.trove.user_revoke_access(IsA(http.HttpRequest),
                                      IsA(six.text_type),
                                      IsA(six.text_type),
                                      [IsA(six.text_type)],
                                      host=IsA(six.text_type)))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:user:access_detail',
                      args=['id', 'name', 'host'])
        form_data = {"action": "access__revoke_access__%s" % 'db1'}
        req = self.factory.post(url, form_data)

        kwargs = {'cluster_id': 'id', 'user_name': 'name', 'user_host': '%'}

        db_access_list = []
        db_access = databases_views.DBAccess('db1', True)
        db_access_list.append(db_access)

        table = tables.AccessTable(req, db_access_list, **kwargs)
        handled = table.maybe_handle()

        handled_url = handled['location']
        self.assertEqual(handled_url, url)

    @test.create_stubs({
        api.trove: ('cluster_get', 'user_delete', 'user_list_access',
                    'users_list',)
    })
    def test_user_delete(self):
        cluster = self.trove_clusters.first()
        user_db = self.database_user_dbs.first()
        users = self.database_users.list()

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(cluster))
        (api.trove.user_delete(IsA(http.HttpRequest),
                               IsA(six.text_type),
                               IsA(six.string_types),
                               host=IsA(six.string_types))
            .AndReturn(None))
        (api.trove.user_list_access(IsA(http.HttpRequest),
                                    IsA(str),
                                    IsA(str),
                                    host=IsA(str)).AndReturn([user_db]))
        (api.trove.users_list(IsA(http.HttpRequest),
                              IsA(six.string_types))
            .AndReturn(users))
        self.mox.ReplayAll()

        res = self.client.post(
            INDEX_URL,
            {'action': 'DataTableOptions__delete_user__%s' % users[0].name})

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({
        api.trove: ('cluster_get', 'user_delete', 'user_list_access',
                    'users_list',)
    })
    def test_user_delete_exception(self):
        cluster = self.trove_clusters.first()
        user_db = self.database_user_dbs.first()
        users = self.database_users.list()

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(cluster))
        (api.trove.user_delete(IsA(http.HttpRequest),
                               IsA(six.text_type),
                               IsA(six.string_types),
                               host=IsA(six.string_types))
            .AndRaise(self.exceptions.trove))
        (api.trove.user_list_access(IsA(http.HttpRequest),
                                    IsA(str),
                                    IsA(str),
                                    host=IsA(str)).AndReturn([user_db]))
        (api.trove.users_list(IsA(http.HttpRequest),
                              IsA(six.string_types))
            .AndReturn(users))
        self.mox.ReplayAll()

        res = self.client.post(
            INDEX_URL,
            {'action': 'DataTableOptions__delete_user__%s' % users[0].name})

        self.assertRedirectsNoFollow(res, INDEX_URL)
