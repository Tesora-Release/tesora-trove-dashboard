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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import validators

from trove_dashboard import api
from trove_dashboard.content.databases import db_capability


TROVE_ENABLE_USER_ROLES = getattr(settings, 'TROVE_ENABLE_USER_ROLES', [])


class CreateUserForm(forms.SelfHandlingForm):
    cluster_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(label=_("Name"))
    password = forms.RegexField(
        label=_("Password"),
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    host = forms.CharField(
        label=_("Host"), required=False, help_text=_("Optional host of user."))
    databases = forms.CharField(
        label=_('Initial Databases'), required=False,
        help_text=_('Optional comma separated list of databases user has '
                    'access to.'))
    roles = forms.CharField(
        label=_('Roles'), required=False,
        help_text=_('Optional comma separated list of roles the user has.'))
    index_url = "horizon:project:database_clusters:user:manage_users"

    def __init__(self, request, *args, **kwargs):
        super(CreateUserForm, self).__init__(request, *args, **kwargs)

        self.datastore = kwargs.get('initial', {}).get('datastore').get('type')
        if self.datastore not in TROVE_ENABLE_USER_ROLES:
            self.fields['roles'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super(CreateUserForm, self).clean()

        if db_capability.is_couchbase_datastore(self.datastore):
            if cleaned_data['roles'] and cleaned_data['roles'] != "read-only":
                msg = _('The only valid role is "read-only".')
                self._errors["roles"] = self.error_class([msg])

        return cleaned_data

    def handle(self, request, data):
        cluster = data.get('cluster_id')
        try:
            api.trove.user_create(
                request,
                cluster,
                data['name'],
                data['password'],
                host=data['host'],
                databases=self._get_databases(data),
                roles=self._get_roles(data))

            messages.success(request,
                             _('Created user "%s".') % data['name'])
        except Exception as e:
            redirect = reverse(self.index_url, args=(cluster,))
            exceptions.handle(request, _('Unable to create user. %s') %
                              e.message, redirect=redirect)
        return True

    def _get_databases(self, data):
        databases = []
        db_value = data['databases']
        if db_value and db_value != u'':
            dbs = data['databases']
            databases = [{'name': d.strip()} for d in dbs.split(',')]
        return databases

    def _get_roles(self, data):
        roles = None
        db_value = data['roles']
        if db_value and db_value != u'':
            roles = [{'name': r.strip()} for r in data['roles'].split(',')]
        return roles


class EditUserForm(forms.SelfHandlingForm):
    cluster_id = forms.CharField(widget=forms.HiddenInput())
    user_name = forms.CharField(
        label=_("Name"),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    user_host = forms.CharField(
        label=_("Host"), required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    new_name = forms.CharField(label=_("New Name"), required=False)
    new_password = forms.RegexField(
        label=_("New Password"), required=False,
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    new_host = forms.CharField(label=_("New Host"), required=False)
    index_url = "horizon:project:database_clusters:user:manage_users"

    validation_error_message = _('A new name or new password or '
                                 'new host must be specified.')

    def handle(self, request, data):
        cluster = data.get('cluster_id')
        try:
            api.trove.user_update_attributes(
                request,
                cluster,
                data['user_name'],
                host=data['user_host'],
                new_name=data['new_name'],
                new_password=data['new_password'],
                new_host=data['new_host'])

            messages.success(request,
                             _('Updated user "%s".') % data['user_name'])
        except Exception as e:
            redirect = reverse(self.index_url, args=(cluster,))
            exceptions.handle(request, _('Unable to update user. %s') %
                              e.message, redirect=redirect)
        return True

    def clean(self):
        cleaned_data = super(EditUserForm, self).clean()

        if (not (cleaned_data['new_name'] or
                 cleaned_data['new_password'] or
                 cleaned_data['new_host'])):
            raise ValidationError(self.validation_error_message)

        return cleaned_data
