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

import json

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms as horizon_forms
from horizon import tables as horizon_tables
from horizon.utils import memoized
from horizon import views

from trove_dashboard import api
from trove_dashboard.content.databases.schedules import forms
from trove_dashboard.content.databases.schedules import tables


class CreateScheduleView(horizon_forms.ModalFormView):
    form_class = forms.CreateScheduleForm
    form_id = "create_schedule_form"
    modal_header = _("Create Backup Schedule")
    modal_id = "create_schedule_modal"
    template_name = 'project/databases/schedules/create_schedule.html'
    submit_label = _("Create Schedule")
    submit_url = 'horizon:project:databases:schedules:create_schedule'
    success_url = 'horizon:project:databases:schedules:view_schedules'
    page_title = _("Create Backup Schedule")

    def get_context_data(self, **kwargs):
        context = (super(CreateScheduleView, self).get_context_data(**kwargs))
        context['instance_id'] = self.kwargs['instance_id']
        args = (self.kwargs['instance_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        initial = super(CreateScheduleView, self).get_initial()
        initial['instance_id'] = self.kwargs['instance_id']
        return initial

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['instance_id'],))


class DetailView(views.APIView):
    template_name = 'project/databases/schedules/detail.html'
    page_title = "Details of Schedule: {{ schedule.name }}"
    preload = False

    def get_data(self, request, context, *args, **kwargs):
        instance_id = self.kwargs['instance_id']
        schedule_id = self.kwargs['schedule_id']
        try:
            schedule = self.get_schedule_detail(request, schedule_id)
            schedule_input = json.loads(schedule.input)
            schedule.description = schedule_input['description']
            context['schedule'] = schedule
        except Exception:
            redirect = reverse(
                "horizon:project:databases:schedules:view_schedules",
                args=(instance_id,))
            msg = (_('Unable to retrieve details for schedule: %s')
                   % schedule_id)
            exceptions.handle(self.request, msg, redirect=redirect)
        return context

    @memoized.memoized_method
    def get_schedule_detail(self, request, schedule_id):
        return api.trove.schedule_show(request,
                                       schedule_id,
                                       api.trove.mistralclient(self.request))


class ViewExecutionsView(horizon_tables.DataTableView):
    table_class = tables.ExecutionsTable
    template_name = 'project/databases/schedules/executions.html'
    page_title = _("Executions of {{schedule.name}} for {{ instance.name }}")
    preload = False

    def get_context_data(self, **kwargs):
        context = super(ViewExecutionsView, self).get_context_data(**kwargs)
        context['instance'] = self.get_instance()
        context['schedule'] = self.get_schedule()
        return context

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        try:
            marker = self.request.GET.get(
                tables.ExecutionsTable._meta.pagination_param)
            executions, self._more = self.get_executions(marker=marker)
        except Exception:
            self._more = False
            executions = []
            msg = _('Unable to retrieve executions list.')
            exceptions.handle(self.request, msg)
        return executions

    @memoized.memoized_method
    def get_instance(self):
        try:
            return api.trove.instance_get(self.request,
                                          self.kwargs['instance_id'])
        except Exception:
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg)

    @memoized.memoized_method
    def get_schedule(self):
        try:
            return api.trove.schedule_show(
                self.request, self.kwargs['schedule_id'],
                api.trove.mistralclient(self.request))
        except Exception:
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg)

    @memoized.memoized_method
    def get_executions(self, marker=''):
        return api.trove.execution_list(self.request,
                                        self.kwargs['schedule_id'],
                                        api.trove.mistralclient(self.request),
                                        marker=marker)


class ViewSchedulesView(horizon_tables.DataTableView):
    table_class = tables.SchedulesTable
    template_name = 'project/databases/schedules/schedules.html'
    page_title = _("Backup Schedules: {{ instance.name }}")
    preload = False

    def get_context_data(self, **kwargs):
        context = super(ViewSchedulesView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        context['instance'] = self.get_instance()
        return context

    def get_data(self):
        try:
            schedules = self.get_schedules()
        except Exception:
            schedules = []
            msg = _('Unable to retrieve schedules list.')
            exceptions.handle(self.request, msg)
        return schedules

    @memoized.memoized_method
    def get_instance(self):
        try:
            return api.trove.instance_get(self.request,
                                          self.kwargs['instance_id'])
        except Exception:
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg)

    @memoized.memoized_method
    def get_schedules(self):
        return api.trove.schedule_list(self.request,
                                       self.kwargs['instance_id'],
                                       api.trove.mistralclient(self.request))
