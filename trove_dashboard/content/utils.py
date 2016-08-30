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


import logging

from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


ACTIVE_STATES = ("ACTIVE",)
STATUS_CHOICES = (
    ("ACTIVE", True),
    ("BLOCKED", True),
    ("BUILD", None),
    ("FAILED", False),
    ("REBOOT", None),
    ("RESIZE", None),
    ("BACKUP", None),
    ("SHUTDOWN", False),
    ("ERROR", False),
    ("RESTART_REQUIRED", None),
)
STATUS_DISPLAY_CHOICES = (
    ("ACTIVE", pgettext_lazy("Current status of a Database Instance",
                             u"Active")),
    ("BLOCKED", pgettext_lazy("Current status of a Database Instance",
                              u"Blocked")),
    ("BUILD", pgettext_lazy("Current status of a Database Instance",
                            u"Build")),
    ("FAILED", pgettext_lazy("Current status of a Database Instance",
                             u"Failed")),
    ("REBOOT", pgettext_lazy("Current status of a Database Instance",
                             u"Reboot")),
    ("RESIZE", pgettext_lazy("Current status of a Database Instance",
                             u"Resize")),
    ("BACKUP", pgettext_lazy("Current status of a Database Instance",
                             u"Backup")),
    ("SHUTDOWN", pgettext_lazy("Current status of a Database Instance",
                               u"Shutdown")),
    ("ERROR", pgettext_lazy("Current status of a Database Instance",
                            u"Error")),
    ("RESTART_REQUIRED",
     pgettext_lazy("Current status of a Database Instance",
                   u"Restart Required")),
)


def volume_type_list(request):
    """Utility method to retrieve a list of volume types."""
    try:
        return api.cinder.volume_type_list(request)
    except Exception:
        exceptions.handle(request,
                          _('Unable to retrieve volume types.'))
        return []


def sort_volume_type_list(request, types):
    """Utility method to sort a list of volume types.
       Returns the available types, sorted by name (ascending).
    """
    try:
        type_list = [(volume_type.id, '%s' % volume_type.name)
                     for volume_type in sorted(types, key=lambda t: t.name)]
        return type_list
    except Exception:
        exceptions.handle(request, _('Unable to sort volume types.'))
        return []


def volume_type_field_data(request, include_empty_option=False):
    """Returns a list of tuples of all volume types.

    Generates a list of volume types available. And returns a list of
    (id, name) tuples.

    :param request: django http request object
    :param include_empty_option: flag to include a empty tuple in the front of
        the list
    :return: list of (id, name) tuples
    """
    types = volume_type_list(request)
    if types:
        types_list = sort_volume_type_list(request, types)
        if include_empty_option:
            return [("", _("Select Volume Type")), ] + types_list
        return types_list

    if include_empty_option:
        return [("", _("No volume types available")), ]
    return []
