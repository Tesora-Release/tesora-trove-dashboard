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

from django.conf.urls import patterns
from django.conf.urls import url

from trove_dashboard.content.databases.couchbase import views


VIEWS_MOD = ('trove_dashboard.content.databases.couchbase.views')

COUCHBASE = r'^(?P<bucket_id>[^/]+)/%s$'

urlpatterns = patterns(
    VIEWS_MOD,
    url(r'^manage_buckets$',
        views.ManageBucketsView.as_view(),
        name='manage_buckets'),
    url(r'^create_bucket$',
        views.CreateBucketView.as_view(),
        name='create_bucket'),
    url(COUCHBASE % 'update_bucket',
        views.UpdateBucketView.as_view(),
        name='update_bucket'),
)
