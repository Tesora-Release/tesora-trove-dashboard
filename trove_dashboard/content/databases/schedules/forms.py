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
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from trove_dashboard import api


class CreateScheduleForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(
        label=_("Name"))
    pattern = forms.CharField(
        label=_("Pattern"),
        help_text=_("Cron pattern for the schedule."))
    description = forms.CharField(
        label=_("Description"),
        required=False)
    incremental = forms.BooleanField(
        widget=forms.CheckboxInput(),
        label=_("Incremental"),
        required=False
    )

    def __init__(self, request, *args, **kwargs):
        super(CreateScheduleForm, self).__init__(request, *args, **kwargs)

        initial = kwargs.get('initial', {})
        self.fields['instance_id'].initial = initial.get('instance_id')

    def handle(self, request, data):
        instance = data.get('instance_id')
        try:
            api.trove.schedule_create(
                request,
                instance,
                data.get('pattern'),
                data.get('name'),
                description=data.get('description'),
                mistral_client=api.trove.mistralclient(self.request),
                incremental=data.get('incremental'))
            messages.success(
                request, _('Creating Schedule "%s"') % data.get('name'))
        except Exception as e:
            redirect = reverse("horizon:project:databases:index")
            exceptions.handle(request,
                              _('Unable to create schedule for instance. %s') %
                              e.message, redirect=redirect)
        return True
