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

"""
Views for displaying database backups.
"""
import json

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django import http
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms as horizon_forms
from horizon import tables as horizon_tables
from horizon.utils import filters
from horizon.utils import memoized
from horizon import views as horizon_views
from horizon import workflows as horizon_workflows

from openstack_dashboard.dashboards.project.containers.views import (
    object_download as dash_containers_object_download)

from trove_dashboard import api
from trove_dashboard.content.database_backups import forms
from trove_dashboard.content.database_backups import tables
from trove_dashboard.content.database_backups \
    import workflows


class IndexView(horizon_tables.DataTableView):
    table_class = tables.BackupsTable
    template_name = 'project/database_backups/index.html'
    page_title = _("Backups")

    def _get_extra_data(self, backup):
        """Apply extra info to the backup."""
        instance_id = backup.instance_id
        # TODO(rdopieralski) It's not clear where this attribute is supposed
        # to come from. At first glance it looks like it will always be {}.
        if not hasattr(self, '_instances'):
            self._instances = {}
        instance = self._instances.get(instance_id)
        if instance is None:
            try:
                instance = self.get_instance(instance_id)
            except Exception:
                instance = _('Not Found')
        backup.instance = instance
        return backup

    def get_data(self):
        # TODO(rmyers) Add pagination support after it is available
        # https://blueprints.launchpad.net/trove/+spec/paginate-backup-list
        try:
            backups = self.get_backups()
            backups = map(self._get_extra_data, backups)
        except Exception:
            backups = []
            msg = _('Error getting database backup list.')
            exceptions.handle(self.request, msg)
        return backups

    @memoized.memoized_method
    def get_backups(self, marker=None):
        return api.trove.backup_list(self.request, marker=marker)

    @memoized.memoized_method
    def get_instance(self, instance_id):
        return api.trove.instance_get(self.request, instance_id)


class BackupView(horizon_workflows.WorkflowView):
    workflow_class = workflows.CreateBackup
    template_name = "project/database_backups/backup.html"
    page_title = _("Backup Database")

    def get_context_data(self, **kwargs):
        context = super(BackupView, self).get_context_data(**kwargs)
        context["instance_id"] = kwargs.get("instance_id")
        self._instance = context['instance_id']
        return context


class DetailView(horizon_views.APIView):
    template_name = "project/database_backups/details.html"
    page_title = _("Backup Details: {{ backup.name }}")

    def get_data(self, request, context, *args, **kwargs):
        backup_id = kwargs.get("backup_id")
        try:
            backup = api.trove.backup_get(request, backup_id)
            created_at = filters.parse_isotime(backup.created)
            updated_at = filters.parse_isotime(backup.updated)
            backup.duration = updated_at - created_at
        except Exception:
            redirect = reverse('horizon:project:database_backups:index')
            msg = _('Unable to retrieve details for backup: %s') % backup_id
            exceptions.handle(self.request, msg, redirect=redirect)

        try:
            if(hasattr(backup, 'parent_id') and backup.parent_id is not None):
                backup.parent = api.trove.backup_get(request, backup.parent_id)
        except Exception:
            redirect = reverse('horizon:project:database_backups:index')
            msg = (_('Unable to retrieve details for parent backup: %s')
                   % backup.parent_id)
            exceptions.handle(self.request, msg, redirect=redirect)

        try:
            instance = api.trove.instance_get(request, backup.instance_id)
        except Exception:
            instance = None
        context['backup'] = backup
        context['instance'] = instance
        return context


class BackupFile(object):
    def __init__(self, name):
        self.name = name


class ExportBackupView(horizon_tables.DataTableView):
    table_class = tables.ExportBackupTable
    template_name = 'project/database_backups/export_backup.html'
    page_title = _("Export Backup")

    @memoized.memoized_method
    def get_data(self):
        backup_id = self.kwargs['backup_id']
        try:
            backup = api.trove.backup_get(self.request, backup_id)
        except Exception:
            redirect = reverse('horizon:project:database_backups:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve backup.'),
                              redirect=redirect)

        backup_name = backup.filename
        backup_files = []
        backup_files.append(BackupFile(backup_name + ".metadata"))
        backup_files.append(BackupFile(backup_name))

        return backup_files

    def get_context_data(self, **kwargs):
        context = super(ExportBackupView, self).get_context_data(**kwargs)
        context["backup_files"] = self.get_data()
        return context


def download_backup_object(request, backup_id):
    backup_info = api.trove.backup_get(request, backup_id)
    return dash_containers_object_download(request,
                                           backup_info.container,
                                           backup_info.filename)


def download_backup_metadata(request, backup_id):
    try:
        backup = api.trove.backup_get(request, backup_id)
        response = http.HttpResponse()
        response.write(json.dumps(backup._info, sort_keys=True))
        backup_filename = backup.filename + ".metadata"
        response['Content-Disposition'] = ('attachment; '
                                           'filename=%s' % backup_filename)
        response['Content-Length'] = str(len(response.content))
        return response
    except Exception:
        redirect = reverse("horizon:project:database_backups:export",
                           args=[backup_id])
        exceptions.handle(request,
                          _("Unable to download backup metadata."),
                          redirect=redirect,)


class ImportBackupView(horizon_forms.ModalFormView):
    form_class = forms.ImportBackupForm
    form_id = "import_backup_form"
    modal_header = _("Import Backup")
    modal_id = "import_backup_modal"
    template_name = 'project/database_backups/import_backup.html'
    submit_label = _("Import Backup")
    submit_url = reverse_lazy('horizon:project:database_backups:import')
    success_url = reverse_lazy('horizon:project:database_backups:index')
    page_title = _("Import Backup")
