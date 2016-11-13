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
from troveclient import common

INDEX_URL = reverse('horizon:project:database_clusters:index')


class ConfigurationsTests(test.TestCase):
    @test.create_stubs({
        api.trove: ('cluster_get',
                    'configuration_list',
                    'cluster_configuration_attach'),
    })
    def test_attach_configuration(self):
        cluster = self.trove_clusters.first()
        configuration = self.database_configurations.list()[2]

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(cluster))
        (api.trove.configuration_list(IsA(http.HttpRequest))
            .AndReturn(self.database_configurations.list()))
        (api.trove.cluster_configuration_attach(IsA(http.HttpRequest),
                                                IsA(six.text_type),
                                                IsA(six.text_type))
            .AndReturn(None))
        self.mox.ReplayAll()

        url = reverse('horizon:project:database_clusters:'
                      'configurations:attach_config',
                      args=[cluster.id])
        form = {
            'cluster_id': cluster.id,
            'configuration': unicode(configuration.id, "utf-8")
        }
        res = self.client.post(url, form)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({
        api.trove: ('cluster_get',
                    'configuration_list',
                    'cluster_configuration_attach'),
    })
    def test_attach_configuration_exception(self):
        cluster = self.trove_clusters.first()
        configuration = self.database_configurations.list()[2]

        (api.trove.cluster_get(IsA(http.HttpRequest),
                               IsA(six.text_type))
            .AndReturn(cluster))
        (api.trove.configuration_list(IsA(http.HttpRequest))
            .AndReturn(self.database_configurations.list()))
        (api.trove.cluster_configuration_attach(IsA(http.HttpRequest),
                                                IsA(six.text_type),
                                                IsA(six.text_type))
            .AndRaise(self.exceptions.trove))

        self.mox.ReplayAll()
        url = reverse('horizon:project:database_clusters:'
                      'configurations:attach_config',
                      args=[cluster.id])
        form = {
            'cluster_id': cluster.id,
            'configuration': unicode(configuration.id, "utf-8")
        }
        res = self.client.post(url, form)

        self.assertEqual(res.status_code, 302)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({
        api.trove: ('cluster_list',
                    'flavor_list',
                    'cluster_configuration_detach',),
    })
    def test_detach_configuration(self):
        clusters = common.Paginated(self.trove_clusters.list())
        cluster = clusters[0]

        (api.trove.cluster_list(IsA(http.HttpRequest),
                                marker=None)
            .MultipleTimes().AndReturn(clusters))
        (api.trove.flavor_list(IsA(http.HttpRequest))
            .MultipleTimes().AndReturn(self.flavors.list()))
        (api.trove.cluster_configuration_detach(IsA(http.HttpRequest),
                                                IsA(six.text_type))
            .AndReturn(None))
        self.mox.ReplayAll()

        res = self.client.post(
            INDEX_URL,
            {'action': 'clusters__detach_configuration__%s' % cluster.id})

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({
        api.trove: ('cluster_list',
                    'flavor_list',
                    'cluster_configuration_detach',),
    })
    def test_detach_configuration_exception(self):
        clusters = common.Paginated(self.trove_clusters.list())
        cluster = clusters[0]

        (api.trove.cluster_list(IsA(http.HttpRequest),
                                marker=None)
            .AndReturn(clusters))
        (api.trove.flavor_list(IsA(http.HttpRequest))
            .AndReturn(self.flavors.list()))
        (api.trove.cluster_configuration_detach(IsA(http.HttpRequest),
                                                IsA(six.text_type))
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()

        res = self.client.post(
            INDEX_URL,
            {'action': 'clusters__detach_configuration__%s' % cluster.id})

        self.assertRedirectsNoFollow(res, INDEX_URL)
