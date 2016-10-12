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

from trove_dashboard import api
from trove_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:database_clusters:index')


class UpgradeTests(test.TestCase):

    @test.create_stubs({
        api.trove: ('cluster_get', 'datastore_version_list')
    })
    def test_upgrade_cluster_get(self):
        cluster = self.trove_clusters.first()

        (api.trove.cluster_get(IsA(http.HttpRequest), cluster.id)
            .AndReturn(cluster))
        (api.trove.datastore_version_list(IsA(http.HttpRequest),
                                          IsA(str))
            .AndReturn(self.datastore_versions.list()))

        self.mox.ReplayAll()
        url = reverse(
            'horizon:project:database_clusters:upgrade:upgrade_cluster',
            args=[cluster.id])

        res = self.client.get(url)
        self.assertTemplateUsed(
            res, 'project/database_clusters/upgrade/upgrade_cluster.html')

    @test.create_stubs({
        api.trove: ('cluster_get', 'cluster_upgrade', 'datastore_version_list')
    })
    def test_upgrade_cluster(self):
        cluster = self.trove_clusters.first()
        datastore_version = self.datastore_versions.first()

        (api.trove.cluster_get(IsA(http.HttpRequest), cluster.id)
            .AndReturn(cluster))
        (api.trove.cluster_upgrade(IsA(http.HttpRequest),
                                   cluster.id,
                                   datastore_version.id)
            .AndReturn(None))
        (api.trove.datastore_version_list(IsA(http.HttpRequest),
                                          IsA(str))
            .AndReturn(self.datastore_versions.list()))

        self.mox.ReplayAll()
        url = reverse(
            'horizon:project:database_clusters:upgrade:upgrade_cluster',
            args=[cluster.id])
        post = {
            'cluster_id': cluster.id,
            'cluster_name': cluster.name,
            'new_datastore_version': datastore_version.id
        }
        res = self.client.post(url, post)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
