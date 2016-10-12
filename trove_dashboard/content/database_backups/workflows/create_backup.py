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

import ast
import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from trove_dashboard import api
from trove_dashboard.content.databases import db_capability
from trove_dashboard.content import utils as database_utils


LOG = logging.getLogger(__name__)


class BackupDetailsAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    instance = forms.ChoiceField(label=_("Database Instance"),
                                 widget=forms.Select(attrs={
                                     'class': 'switchable',
                                     'data-slug': 'instance'
                                 }))
    description = forms.CharField(max_length=512, label=_("Description"),
                                  widget=forms.TextInput(),
                                  required=False,
                                  help_text=_("Optional Backup Description"))

    class Meta(object):
        name = _("Details")
        help_text_template = \
            "project/database_backups/_backup_details_help.html"

    def __init__(self, request, *args, **kwargs):
        if args[0]:
            self.current_instance_id = args[0].get('instance', None)
        else:
            self.current_instance_id = None

        if hasattr(request, "GET"):
            self.include_clustered = ast.literal_eval(
                request.GET.get('include_clustered', 'False'))
        else:
            self.include_clustered = False

        super(BackupDetailsAction, self).__init__(request, *args, **kwargs)

    def handle(self, request, context):
        instance = context["instance"]
        if instance:
            instance_id = database_utils.parse_instance_text(instance)
            if instance_id:
                context["instance"] = instance_id

                field_name = database_utils.build_parent_backup_field_name(
                    instance_id)
                # field_name = 'parent-' + instance
                if field_name in self.data:
                    parent = self.data[field_name]
                    if parent:
                        context["parent"] = parent

                return context
        return None

    def populate_instance_choices(self, request, context):
        LOG.info("Obtaining list of instances.")
        try:
            choices = []
            instances = api.trove.instance_list_all(
                request, include_clustered=self.include_clustered)
            for instance in instances:
                if (self.current_instance_id and
                        self.current_instance_id != instance.id):
                    continue

                if (instance.status in database_utils.ACTIVE_STATES and
                        db_capability.can_backup(instance.datastore['type'])):
                    self._add_parent_backup_field(request, instance)
                    choices.append(
                        (database_utils.build_instance_widget_field_name(
                            instance.id),
                         instance.name))
        except Exception:
            choices = []
            msg = _("Unable to list database instances to backup.")
            exceptions.handle(request, msg)
        return choices

    def _add_parent_backup_field(self, request, instance):
        name = database_utils.build_instance_widget_field_name(instance.id)
        attr_key = 'data-instance-' + name
        field_name = database_utils.build_parent_backup_field_name(instance.id)

        self.fields[field_name] = forms.ChoiceField(
            label=_("Parent Backup"),
            required=False,
            help_text=_("Optional parent backup"),
            widget=forms.Select(attrs={
                'class': 'switched',
                'data-switch-on': 'instance',
                attr_key: _("Parent Backup")
            }))

        try:
            valid_backups = api.trove.instance_backups(request, instance)
            choices = [(b.id, b.name) for b in valid_backups
                       if (b.status == 'COMPLETED') and
                       (db_capability.can_backup(b.datastore['type']))]
        except Exception:
            choices = []
            msg = _("Unable to list database backups for instance.")
            exceptions.handle(request, msg)

        if choices:
            choices.insert(0, ("", _("Select parent backup")))
        else:
            choices.insert(0, ("", _("No backups available")))

        self.fields[field_name].choices = choices


class SetBackupDetails(workflows.Step):
    action_class = BackupDetailsAction
    contributes = ["name", "description", "instance", "parent"]


class CreateBackup(workflows.Workflow):
    slug = "create_backup"
    name = _("Backup Database")
    finalize_button_name = _("Backup")
    success_message = _('Scheduled backup "%(name)s".')
    failure_message = _('Unable to create backup for "%(name)s".')
    success_url = "horizon:project:database_backups:index"
    default_steps = [SetBackupDetails]

    def get_initial(self):
        initial = super(CreateBackup, self).get_initial()
        initial['instance_id']

    def get_absolute_url(self):
        return self.request.get_full_path()

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown instance')
        return message % {"count": _("instance"), "name": name}

    def handle(self, request, context):
        try:
            LOG.info("Creating backup")
            api.trove.backup_create(request,
                                    context['name'],
                                    context['instance'],
                                    context['description'],
                                    context['parent'])
            return True
        except Exception as e:
            LOG.exception("Exception while creating backup")
            msg = _('Cannot create database backup: %s') % e.message
            exceptions.handle(request, msg)
            return False
