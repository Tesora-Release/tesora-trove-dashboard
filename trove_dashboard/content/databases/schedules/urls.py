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

from trove_dashboard.content.databases.schedules import views


VIEWS_MOD = ('trove_dashboard.content.databases.schedules.views')

SCHEDULE = r'^(?P<schedule_id>[^/]+)/%s$'

urlpatterns = patterns(
    VIEWS_MOD,
    url(r'^create_schedule$',
        views.CreateScheduleView.as_view(),
        name='create_schedule'),
    url(r'^view_schedules$',
        views.ViewSchedulesView.as_view(),
        name='view_schedules'),
    url(SCHEDULE % 'schedule_detail',
        views.DetailView.as_view(),
        name='schedule_detail'),
    url(SCHEDULE % 'view_executions',
        views.ViewExecutionsView.as_view(),
        name='view_executions'),
)
