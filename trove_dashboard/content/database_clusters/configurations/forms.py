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


class AttachConfigurationForm(forms.SelfHandlingForm):
    cluster_id = forms.CharField(widget=forms.HiddenInput())
    configuration = forms.ChoiceField(label=_("Configuration Group"))

    def __init__(self, request, *args, **kwargs):
        super(AttachConfigurationForm, self).__init__(request, *args, **kwargs)
        cluster_id = kwargs.get('initial', {}).get('cluster_id')
        datastore = kwargs.get('initial', {}).get('datastore')
        datastore_version = kwargs.get('initial', {}).get('datastore_version')
        self.fields['cluster_id'].initial = cluster_id

        configurations = api.trove.configuration_list(request)
        choices = [(c.id, c.name) for c in configurations
                   if (c.datastore_name == datastore and
                       c.datastore_version_name == datastore_version)]
        if choices:
            choices.insert(0, ("", _("Select configuration group")))
        else:
            choices.insert(0, ("", _("No configuration groups available")))
        self.fields['configuration'].choices = choices

    def handle(self, request, data):
        cluster_id = data.get('cluster_id')
        try:
            api.trove.cluster_configuration_attach(request,
                                                   cluster_id,
                                                   data['configuration'])

            messages.success(request, _('Attaching Configuration group "%s"')
                             % cluster_id)
        except Exception as e:
            redirect = reverse("horizon:project:database_clusters:index")
            exceptions.handle(request,
                              _('Unable to attach configuration group. %s')
                              % e.message, redirect=redirect)
        return True
