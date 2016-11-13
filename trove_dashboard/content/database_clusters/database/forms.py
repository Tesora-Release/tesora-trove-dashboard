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
from trove_dashboard.content.databases import db_capability


class CreateDatabaseForm(forms.SelfHandlingForm):
    cluster_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(label=_("Name"))
    character_set = forms.CharField(
        label=_("Character Set"), required=False,
        help_text=_("Optional character set for the database."))
    collation = forms.CharField(
        label=_("Collation"), required=False,
        help_text=_("Optional collation type for the database."))
    index_url = "horizon:project:database_clusters:database:manage_databases"

    def __init__(self, request, *args, **kwargs):
        super(CreateDatabaseForm, self).__init__(request, *args, **kwargs)

        datastore = kwargs.get('initial', {}).get('datastore').get('type')
        if not db_capability.is_mysql_compatible(datastore):
            self.fields['character_set'].widget = forms.HiddenInput()
            self.fields['collation'].widget = forms.HiddenInput()

    def handle(self, request, data):
        cluster = data.get('cluster_id')
        try:
            api.trove.database_create(request, cluster, data['name'],
                                      character_set=data['character_set'],
                                      collation=data['collation'])

            messages.success(request,
                             _('Created database "%s".') % data['name'])
        except Exception as e:
            redirect = reverse(self.index_url, args=(cluster,))
            exceptions.handle(request, _('Unable to create database. %s') %
                              e.message, redirect=redirect)
        return True
