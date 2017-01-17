# Copyright 2013 Rackspace Hosting
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

from trove_dashboard.content.database_backups import views

urlpatterns = patterns(
    '',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create$', views.BackupView.as_view(), name='create'),
    url(r'^import$', views.ImportBackupView.as_view(), name='import'),
    url(r'^(?P<backup_id>[^/]+)/$', views.DetailView.as_view(),
        name='detail'),
    url(r'^(?P<backup_id>[^/]+)/export$',
        views.ExportBackupView.as_view(),
        name='export'),
    url(r'^(?P<backup_id>[^/]+)/download_backup$',
        views.download_backup_object,
        name='download_backup'),
    url(r'^(?P<backup_id>[^/]+)/download_metadata$',
        views.download_backup_metadata,
        name='download_metadata'),
)
