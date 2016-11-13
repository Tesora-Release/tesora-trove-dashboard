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

from trove_dashboard.content.database_clusters.user import views


VIEWS_MOD = ('trove_dashboard.content.database_clusters.user.views')

USERS = (r'^(?P<user_name>[^/]+)/(?P<user_host>[^/]+)/%s$')

urlpatterns = patterns(
    VIEWS_MOD,
    url(r'^create_user$',
        views.CreateUserView.as_view(),
        name='create_user'),
    url(r'^manage_users$',
        views.ManageUsersView.as_view(),
        name='manage_users'),
    url(USERS % 'access_detail',
        views.AccessDetailView.as_view(),
        name='access_detail'),
    url(USERS % 'edit_user',
        views.EditUserView.as_view(),
        name='edit_user'),
)
