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

from django.core import urlresolvers
from django.template import defaultfilters as django_filters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from horizon.utils import filters

import json

from trove_dashboard import api
from trove_dashboard.content import utils as database_utils


class ViewSchedules(tables.LinkAction):
    name = "view_schedules"
    verbose_name = _("Scheduled Backups")
    url = "horizon:project:databases:schedules:view_schedules"

    def allowed(self, request, instance):
        return instance.status in database_utils.ACTIVE_STATES

    def get_link_url(self, datum):
        instance_id = self.table.get_object_id(datum)
        return urlresolvers.reverse(self.url, args=[instance_id])


class DeleteExecution(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Execution",
            u"Delete Executions",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Execution",
            u"Scheduled deletion of Executions",
            count
        )

    name = "delete"
    classes = ("btn-danger", )
    icon = "remove"

    def action(self, request, obj_id):
        api.trove.execution_delete(request,
                                   obj_id,
                                   api.trove.mistralclient(request))


class ExecutionsTable(tables.DataTable):
    id = tables.Column(
        "id",
        verbose_name=_("ID"))
    created_at = tables.Column(
        "created_at",
        filters=[filters.parse_isotime],
        verbose_name=_("Execution Time"))
    state = tables.Column(
        "state",
        verbose_name=_("State"))
    output = tables.Column(
        "output",
        verbose_name=_("Output"),
        truncate=200)

    class Meta(object):
        name = "executions"
        verbose_name = _("Backup Executions")
        table_actions = (DeleteExecution,)
        row_actions = (DeleteExecution,)


class CreateSchedule(tables.LinkAction):
    name = "create_schedule_action"
    verbose_name = _("Schedule Backup")
    url = "horizon:project:databases:schedules:create_schedule"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum=None):
        instance_id = self.table.kwargs['instance_id']
        return urlresolvers.reverse(self.url, args=[instance_id])


class DeleteSchedule(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Schedule",
            u"Delete Schedules",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Schedule",
            u"Scheduled deletion of Schedules",
            count
        )

    name = "delete"
    classes = ("btn-danger", )
    icon = "remove"

    def action(self, request, obj_id):
        api.trove.schedule_delete(request,
                                  obj_id,
                                  api.trove.mistralclient(request))


class ViewExecutions(tables.LinkAction):
    name = "view_executions"
    verbose_name = _("View Executions")
    url = "horizon:project:databases:schedules:view_executions"

    def get_link_url(self, datum):
        instance_id = self.table.kwargs['instance_id']
        schedule = datum
        return urlresolvers.reverse(self.url, args=[instance_id,
                                                    schedule.id])


def get_schedule_detail_link(schedule):
    return urlresolvers.reverse(
        "horizon:project:databases:schedules:schedule_detail",
        args=(schedule.instance, schedule.id,))


def is_incremental(obj):
    if hasattr(obj, 'input'):
        input = json.loads(obj.input)
        if 'incremental' in input and input['incremental']:
            return True
    return False


class SchedulesTable(tables.DataTable):
    id = tables.Column(
        "id",
        verbose_name=_("ID"))
    name = tables.Column(
        "name",
        link=get_schedule_detail_link,
        verbose_name=_("Name"))
    pattern = tables.Column(
        "pattern",
        verbose_name=_("Pattern"))
    incremental = tables.Column(
        is_incremental,
        verbose_name=_("Incremental"),
        filters=(django_filters.yesno, django_filters.capfirst))
    next_execution_time = tables.Column(
        "next_execution_time",
        filters=[filters.parse_isotime],
        verbose_name=_("Next Execution Time"))

    class Meta(object):
        name = "schedules"
        verbose_name = _("Backup Schedules")
        table_actions = (CreateSchedule, DeleteSchedule,)
        row_actions = (ViewExecutions, DeleteSchedule)
