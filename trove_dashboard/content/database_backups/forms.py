# Copyright 2017 Tesora Inc.
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
from horizon import forms
from horizon import messages

from openstack_dashboard import api as horizon_api

from trove_dashboard import api


class ImportBackupForm(forms.SelfHandlingForm):
    metadata_file = forms.FileField(label=_("Backup Metadata File"),
                                    required=True,
                                    allow_empty_file=True)
    backup_file = forms.FileField(label=_("Backup File"),
                                  required=False,
                                  allow_empty_file=True)

    def handle(self, request, data):
        metadata_file = self.files['metadata_file']
        backup_file = self.files.get('backup_file', None)

        redirect = reverse("horizon:project:database_backups:index")
        try:
            metadata = json.loads(metadata_file.read())
            if 'description' in metadata and metadata['description'] is None:
                del metadata['description']
            backup = api.trove.import_from_metadata(request, metadata)
        except Exception:
            exceptions.handle(request,
                              _("Unable to import metadata."),
                              redirect=redirect)

        try:
            if backup_file:
                if not horizon_api.swift.swift_container_exists(
                    request, backup.container):
                    horizon_api.swift.swift_create_container(request,
                                                             backup.container)

                horizon_api.swift.swift_upload_object(request,
                                                      backup.container,
                                                      backup.filename,
                                                      backup_file)
        except Exception:
            exceptions.handle(request,
                              _("Unable to import backup."),
                              redirect=redirect)

        messages.success(request, _("Backup was successfully imported."))
        return True
