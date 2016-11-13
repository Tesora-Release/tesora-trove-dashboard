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

import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized
from horizon import workflows
from openstack_dashboard import api as dash_api
from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils
from openstack_dashboard.dashboards.project.instances.workflows \
    import create_instance as dash_create_instance

import re

from trove_dashboard import api
from trove_dashboard.content.databases import db_capability
from trove_dashboard.content import utils

LOG = logging.getLogger(__name__)


config_fields = {}


class SetInstanceDetailsAction(workflows.Action):
    availability_zone = forms.ChoiceField(
        label=_("Availability Zone"),
        required=False)
    name = forms.CharField(max_length=80, label=_("Instance Name"))
    volume = forms.IntegerField(label=_("Volume Size"),
                                min_value=0,
                                initial=getattr(settings,
                                                "TROVE_DEFAULT_VOL_SIZE",
                                                1),
                                help_text=_("Size of the volume in GB."))
    datastore = forms.ChoiceField(
        label=_("Datastore"),
        help_text=_("Type and version of datastore."),
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'datastore'
        }))

    def __init__(self, request, *args, **kwargs):
        if args:
            self.backup_id = args[0].get('backup', None)
        else:
            self.backup_id = None

        super(SetInstanceDetailsAction, self).__init__(request,
                                                       *args,
                                                       **kwargs)

    class Meta(object):
        name = _("Details")
        help_text_template = "project/databases/_launch_details_help.html"

    def clean(self):
        datastore_and_version = self.data.get("datastore", None)
        if not datastore_and_version:
            msg = _("You must select a datastore type and version.")
            self._errors["datastore"] = self.error_class([msg])
        else:
            datastore, datastore_version = (
                utils.parse_datastore_and_version_text(datastore_and_version))
            field_name = utils.build_flavor_field_name(datastore,
                                                       datastore_version)
            flavor = self.data.get(field_name, None)
            if not flavor:
                msg = _("You must select a flavor.")
                self._errors[field_name] = self.error_class([msg])

        return self.cleaned_data

    def handle(self, request, context):
        datastore_and_version = context["datastore"]
        if datastore_and_version:
            datastore, datastore_version = (
                utils.parse_datastore_and_version_text(context["datastore"]))
            field_name = utils.build_flavor_field_name(datastore,
                                                       datastore_version)
            flavor = self.data[field_name]
            if flavor:
                context["flavor"] = flavor

            volume_type_field_name = utils.build_volume_type_field_name(
                datastore, datastore_version)
            volume_type = self.data.get(volume_type_field_name, None)
            if volume_type:
                context["volume_type"] = volume_type

            return context
        return None

    @memoized.memoized_method
    def availability_zones(self, request):
        try:
            return dash_api.nova.availability_zone_list(request)
        except Exception:
            LOG.exception("Exception while obtaining availablity zones")
            self._availability_zones = []

    def populate_availability_zone_choices(self, request, context):
        try:
            zones = self.availability_zones(request)
        except Exception:
            zones = []
            redirect = reverse('horizon:project:databases:index')
            exceptions.handle(request,
                              _('Unable to retrieve availability zones.'),
                              redirect=redirect)

        zone_list = [(zone.zoneName, zone.zoneName)
                     for zone in zones if zone.zoneState['available']]
        zone_list.sort()
        if not zone_list:
            zone_list.insert(0, ("", _("No availability zones found")))
        elif len(zone_list) > 1:
            zone_list.insert(0, ("", _("Any Availability Zone")))
        return zone_list

    @memoized.memoized_method
    def datastore_flavors(self, request, datastore_name, datastore_version):
        try:
            return api.trove.datastore_flavors(
                request, datastore_name, datastore_version)
        except Exception:
            LOG.exception("Exception while obtaining flavors list")
            redirect = reverse("horizon:project:databases:index")
            exceptions.handle(request,
                              _('Unable to obtain flavors.'),
                              redirect=redirect)

    @memoized.memoized_method
    def datastore_volume_types(self, request, datastore_name,
                               datastore_version):
        try:
            return api.trove.datastore_volume_types(
                request, datastore_name, datastore_version)
        except Exception:
            LOG.exception("Exception while obtaining volume types list")
            self._volume_types = []
            redirect = reverse('horizon:project:databases:index')
            exceptions.handle(request,
                              _('Unable to obtain volume types.'),
                              redirect=redirect)

    @memoized.memoized_method
    def datastores(self, request):
        try:
            return api.trove.datastore_list(request)
        except Exception:
            LOG.exception("Exception while obtaining datastores list")
            self._datastores = []

    @memoized.memoized_method
    def datastore_versions(self, request, datastore):
        try:
            return api.trove.datastore_version_list(request, datastore)
        except Exception:
            LOG.exception("Exception while obtaining datastore version list")
            self._datastore_versions = []

    @memoized.memoized_method
    def get_backup(self, request, backup_id):
        try:
            return api.trove.backup_get(request, backup_id)
        except Exception:
            LOG.exception("Exception while obtaining backup information")
            return None

    @memoized.memoized_method
    def populate_config_choices(self, request, datastore, datastore_version):
        try:
            configs = api.trove.configuration_list(request)
            config_name = "%(name)s (%(datastore)s - %(version)s)"
            choices = [(c.id,
                        config_name % {'name': c.name,
                                       'datastore': c.datastore_name,
                                       'version': c.datastore_version_name})
                       for c in configs
                       if (c.datastore_name == datastore and
                           c.datastore_version_name == datastore_version)]
        except Exception:
            choices = []

        if choices:
            choices.insert(0, ("", _("Select configuration")))
        else:
            choices.insert(0, ("", _("No configurations available")))
        return choices

    def populate_datastore_choices(self, request, context):
        config_fields.clear()
        choices = ()
        datastores = self.datastores(request)
        if datastores is not None:
            if self.backup_id:
                backup = self.get_backup(request, self.backup_id)
            for ds in datastores:
                if self.backup_id:
                    if ds.name != backup.datastore['type']:
                        continue
                versions = self.datastore_versions(request, ds.name)
                if versions:
                    # only add to choices if datastore has at least one version
                    version_choices = ()
                    for v in versions:
                        if hasattr(v, 'active') and not v.active:
                            continue
                        if self.backup_id:
                            if v.id != backup.datastore['version_id']:
                                continue
                        selection_text = utils.build_datastore_display_text(
                            ds.name, v.name)
                        widget_text = utils.build_widget_field_name(
                            ds.name, v.name)
                        version_choices = (version_choices +
                                           ((widget_text, selection_text),))
                        self._add_datastore_flavor_field(request,
                                                         ds.name,
                                                         v.name)
                        self._add_datastore_volume_type_field(request,
                                                              ds.name,
                                                              v.name)
                        self._add_datastore_config_field_to_dict(request,
                                                                 ds.name,
                                                                 v.name)
                    choices = choices + version_choices
        return choices

    def _add_datastore_flavor_field(self,
                                    request,
                                    datastore,
                                    datastore_version):
        name = utils.build_widget_field_name(datastore, datastore_version)
        attr_key = 'data-datastore-' + name
        field_name = utils.build_flavor_field_name(datastore,
                                                   datastore_version)
        self.fields[field_name] = forms.ChoiceField(
            label=_("Flavor"),
            help_text=_("Size of image to launch."),
            required=False,
            widget=forms.Select(attrs={
                'class': 'switched',
                'data-switch-on': 'datastore',
                attr_key: _("Flavor")
            }))
        valid_flavors = self.datastore_flavors(request,
                                               datastore,
                                               datastore_version)
        if valid_flavors:
            self.fields[field_name].choices = instance_utils.sort_flavor_list(
                request, valid_flavors)

    def _add_datastore_volume_type_field(self,
                                         request,
                                         datastore,
                                         datastore_version):
        name = utils.build_widget_field_name(datastore, datastore_version)
        attr_key = 'data-datastore-' + name
        field_name = utils.build_volume_type_field_name(datastore,
                                                        datastore_version)
        self.fields[field_name] = forms.ChoiceField(
            label=_("Volume Type"),
            help_text=_("Applicable only if the volume size is specified."),
            required=False,
            widget=forms.Select(attrs={
                'class': 'switched',
                'data-switch-on': 'datastore',
                attr_key: _("Volume Type")
            }))
        valid_types = self.datastore_volume_types(request,
                                                  datastore,
                                                  datastore_version)
        if valid_types:
            self.fields[field_name].choices = (
                utils.sort_volume_type_list(request, valid_types))

    def _add_datastore_config_field_to_dict(self,
                                            request,
                                            datastore,
                                            datastore_version):
        name = utils.build_widget_field_name(datastore, datastore_version)
        attr_key = 'data-datastore-' + name
        field_name = utils.build_config_field_name(datastore,
                                                   datastore_version)
        config_fields[field_name] = forms.ChoiceField(
            label=_("Configuration Group"),
            required=False,
            help_text=_('Select a configuration group'),
            widget=forms.Select(attrs={
                'class': 'switched',
                'data-switch-on': 'datastore',
                attr_key: _("Configuration Group")
            }))
        config_fields[field_name].choices = self.populate_config_choices(
            request, datastore, datastore_version)


TROVE_ENABLE_ORACLE_DATABASE_NAME_VALIDATION = getattr(settings,
                                                       'FORCE_ORACLE_DATABASE',
                                                       False)
TROVE_ADD_USER_PERMS = getattr(settings, 'TROVE_ADD_USER_PERMS', [])
TROVE_ADD_DATABASE_PERMS = getattr(settings, 'TROVE_ADD_DATABASE_PERMS', [])
TROVE_ADD_PERMS = TROVE_ADD_USER_PERMS + TROVE_ADD_DATABASE_PERMS


class SetInstanceDetails(workflows.Step):
    action_class = SetInstanceDetailsAction
    contributes = ("name", "volume", "volume_type", "flavor", "datastore",
                   "availability_zone")


class AddDatabasesAction(workflows.Action):
    """Initialize the database with users/databases. This tab will honor
    the settings which should be a list of permissions required:

    * TROVE_ADD_USER_PERMS = []
    * TROVE_ADD_DATABASE_PERMS = []
    """
    databases = forms.CharField(label=_('Initial Databases'),
                                required=False,
                                help_text=_('Comma separated list of '
                                            'databases to create'))
    user = forms.CharField(label=_('Initial Admin User'),
                           required=False,
                           help_text=_("Initial admin user to add"))
    password = forms.CharField(widget=forms.PasswordInput(),
                               label=_("Password"),
                               required=False)
    host = forms.CharField(label=_("Allowed Host (optional)"),
                           required=False,
                           help_text=_("Host or IP that the user is allowed "
                                       "to connect through."))

    class Meta(object):
        name = _("Initialize Databases")
        permissions = TROVE_ADD_PERMS
        help_text_template = "project/databases/_launch_initialize_help.html"

    def clean(self):
        cleaned_data = super(AddDatabasesAction, self).clean()
        datastore, datastore_version = (
            utils.parse_datastore_and_version_text(
                self.data[u'datastore']))

        if (TROVE_ENABLE_ORACLE_DATABASE_NAME_VALIDATION and
                db_capability.is_oracle_compatible_datastore(datastore)):
            databases = cleaned_data.get('databases')
            if not databases:
                msg = _('You must specify a database name.')
                self._errors["databases"] = self.error_class([msg])
            elif len(databases) > 8:
                msg = _("Database name cannot exceed 8 characters.")
                self._errors["databases"] = self.error_class([msg])
            elif not re.match(r'[a-zA-Z0-9]\w+$', databases):
                msg = _("Database name contains invalid characters.")
                self._errors["databases"] = self.error_class([msg])

        if cleaned_data.get('user'):
            if not cleaned_data.get('password'):
                msg = _('You must specify a password if you create a user.')
                self._errors["password"] = self.error_class([msg])
        return cleaned_data


class InitializeDatabase(workflows.Step):
    action_class = AddDatabasesAction
    contributes = ["databases", 'user', 'password', 'host']


class AdvancedAction(workflows.Action):
    initial_state = forms.ChoiceField(
        label=_('Source for Initial State'),
        required=False,
        help_text=_("Choose initial state."),
        choices=[
            ('', _('None')),
            ('backup', _('Restore from Backup')),
            ('master', _('Replicate from Instance'))],
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'initial_state'
        }))
    backup = forms.ChoiceField(
        label=_('Backup Name'),
        required=False,
        help_text=_('Select a backup to restore'),
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'initial_state',
            'data-initial_state-backup': _('Backup Name')
        }))
    master = forms.ChoiceField(
        label=_('Master Instance Name'),
        required=False,
        help_text=_('Select a master instance'),
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'initial_state',
            'data-initial_state-master': _('Master Instance Name')
        }))
    replica_count = forms.IntegerField(
        label=_('Replica Count'),
        required=False,
        min_value=1,
        initial=1,
        help_text=_('Specify the number of replicas to be created'),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'initial_state',
            'data-initial_state-master': _('Replica Count')
        }))
    region = forms.ChoiceField(
        label=_("Region"),
        required=False)
    locality = forms.ChoiceField(
        label=_("Locality"),
        choices=[("", "None"),
                 ("affinity", "affinity"),
                 ("anti-affinity", "anti-affinity")],
        required=False,
        help_text=_("Specify whether future replicated instances will "
                    "be created on the same hypervisor (affinity) or on "
                    "different hypervisors (anti-affinity).  "
                    "This value is ignored if the instance to be "
                    "launched is a replica."))

    def __init__(self, request, *args, **kwargs):
        if args[0]:
            self.backup_id = args[0].get('backup', None)
        else:
            self.backup_id = None

        super(AdvancedAction, self).__init__(request, *args, **kwargs)

        if config_fields:
            for k, v in config_fields.iteritems():
                self.fields[k] = v

        if not getattr(settings, 'DATABASE_ENABLE_REGION_SUPPORT', False):
            self.fields['region'].widget = forms.HiddenInput()

        if self.backup_id:
            self.fields['initial_state'].choices = [('backup',
                                                    _('Restore from Backup'))]

    class Meta(object):
        name = _("Advanced")
        help_text_template = "project/databases/_launch_advanced_help.html"

    def populate_backup_choices(self, request, context):
        try:
            choices = []
            backups = api.trove.backup_list(request)
            for b in backups:
                if self.backup_id and b.id != self.backup_id:
                    continue
                if b.status == 'COMPLETED':
                    choices.append((b.id, b.name))
        except Exception:
            choices = []

        if choices:
            choices.insert(0, ("", _("Select backup")))
        else:
            choices.insert(0, ("", _("No backups available")))
        return choices

    def _get_instances(self):
        instances = []
        try:
            instances = api.trove.instance_list_all(self.request)
        except Exception:
            msg = _('Unable to retrieve database instances.')
            exceptions.handle(self.request, msg)
        return instances

    def populate_master_choices(self, request, context):
        try:
            instances = self._get_instances()
            choices = sorted([(i.id, i.name) for i in
                             instances if i.status == 'ACTIVE'],
                             key=lambda i: i[1])
        except Exception:
            choices = []

        if choices:
            choices.insert(0, ("", _("Select instance")))
        else:
            choices.insert(0, ("", _("No instances available")))
        return choices

    @memoized.memoized_method
    def regions(self, request):
        try:
            return api.trove.region_list(request)
        except Exception:
            LOG.exception("Exception while obtaining list of regions")
            self._regions = []

    def populate_region_choices(self, request, context):
        try:
            regions = self.regions(request)
        except Exception:
            regions = []
            redirect = reverse('horizon:project:databases:index')
            exceptions.handle(request,
                              _('Unable to retrieve region list.'),
                              redirect=redirect)
        available_regions = [(region, region) for region in regions]
        if not available_regions:
            available_regions.insert(0, ("", _("No regions found")))
        elif len(available_regions) > 1:
            available_regions.insert(0, ("", _("Default region")))
        return available_regions

    def clean(self):
        cleaned_data = super(AdvancedAction, self).clean()

        datastore, datastore_version = (
            utils.parse_datastore_and_version_text(self.data[u'datastore']))

        field_name = utils.build_config_field_name(datastore,
                                                   datastore_version)
        config = self.data.get(field_name, None)
        if config:
            try:
                # Make sure the user is not "hacking" the form
                # and that they have access to this configuration
                cfg = api.trove.configuration_get(self.request, config)
                self.cleaned_data['config'] = cfg.id
            except Exception:
                raise forms.ValidationError(_("Unable to find configuration "
                                              "group!"))
        else:
            if db_capability.require_configuration_group(datastore):
                msg = _('This datastore requires a configuration group.')
                self._errors["config"] = self.error_class([msg])

        initial_state = cleaned_data.get("initial_state")

        if initial_state == 'backup':
            cleaned_data['replica_count'] = None
            if not db_capability.can_backup(datastore):
                msg = _('You cannot specify a backup for the initial state '
                        'for this datastore.')
                self._errors["initial_state"] = self.error_class([msg])
            else:
                backup = self.cleaned_data['backup']
                if backup:
                    try:
                        bkup = api.trove.backup_get(self.request, backup)
                        self.cleaned_data['backup'] = bkup.id
                    except Exception:
                        raise forms.ValidationError(
                            _("Unable to find backup!"))
                else:
                    raise forms.ValidationError(
                        _("A backup must be selected!"))

            cleaned_data['master'] = None
        elif initial_state == 'master':
            if not db_capability.can_launch_from_master(datastore):
                msg = _('You cannot specify a master for the initial state '
                        'for this datastore.')
                self._errors["initial_state"] = self.error_class([msg])
            else:
                master = self.cleaned_data['master']
                if master:
                    try:
                        api.trove.instance_get(self.request, master)
                    except Exception:
                        raise forms.ValidationError(
                            _("Unable to find master instance!"))
                else:
                    raise forms.ValidationError(
                        _("A master instance must be selected!"))

                cleaned_data['backup'] = None
        else:
            cleaned_data['master'] = None
            cleaned_data['backup'] = None
            cleaned_data['replica_count'] = None

        if not self.data.get("locality", None):
            cleaned_data["locality"] = None

        return cleaned_data

    def handle(self, request, context):
        datastore_and_version = context["datastore"]
        if datastore_and_version:
            datastore, datastore_version = (
                utils.parse_datastore_and_version_text(context["datastore"]))
            field_name = utils.build_config_field_name(datastore,
                                                       datastore_version)
            config = self.data.get(field_name, None)
            if config:
                context["config"] = config

        return context


class Advanced(workflows.Step):
    action_class = AdvancedAction
    contributes = ['config', 'backup', 'master', 'replica_count', 'region',
                   'locality']


class LaunchInstance(workflows.Workflow):
    slug = "launch_instance"
    name = _("Launch Instance")
    finalize_button_name = _("Launch")
    success_message = _('Launched %(count)s named "%(name)s".')
    failure_message = _('Unable to launch %(count)s named "%(name)s".')
    success_url = "horizon:project:databases:index"
    default_steps = (SetInstanceDetails,
                     dash_create_instance.SetNetwork,
                     InitializeDatabase,
                     Advanced)

    def __init__(self, request=None, context_seed=None, entry_point=None,
                 *args, **kwargs):
        super(LaunchInstance, self).__init__(request, context_seed,
                                             entry_point, *args, **kwargs)
        self.attrs['autocomplete'] = (
            settings.HORIZON_CONFIG.get('password_autocomplete'))

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown instance')
        return message % {"count": _("instance"), "name": name}

    def _get_databases(self, context):
        """Returns the initial databases for this instance."""
        databases = []
        if context.get('databases'):
            dbs = context['databases']
            databases = [{'name': d.strip()} for d in dbs.split(',')]
        return databases

    def _get_users(self, context):
        users = None
        if context.get('user'):
            user = {
                'name': context['user'],
                'password': context['password'],
                'databases': self._get_databases(context),
            }
            if context['host']:
                user['host'] = context['host']
            users = [user]
        return users

    def _get_backup(self, context):
        backup = None
        if context.get('backup'):
            backup = {'backupRef': context['backup']}
        return backup

    def _get_nics(self, context):
        netids = context.get('network_id', None)
        if netids:
            return [{"net-id": netid, "v4-fixed-ip": ""}
                    for netid in netids]
        else:
            return None

    def _get_config(self, context):
        config = None
        if context.get('config'):
            config = context['config']
        return config

    def _get_volume_type(self, context):
        volume_type = None
        if context.get('volume_type') != 'no_type':
            volume_type = context['volume_type']
        return volume_type

    def _get_locality(self, context):
        # if creating a replica from a master then always set to None
        if context.get('master'):
            return None

        locality = None
        if context.get('locality'):
            locality = context['locality']
        return locality

    def _get_region(self, context):
        region = None
        if context.get('region'):
            region = context['region']
        return region

    def handle(self, request, context):
        try:
            avail_zone = context.get('availability_zone', None)

            datastore, datastore_version = (
                utils.parse_datastore_and_version_text(
                    self.context['datastore']))
            LOG.info("Launching database instance with parameters "
                     "{name=%s, volume=%s, volume_type=%s, flavor=%s, "
                     "datastore=%s, datastore_version=%s, "
                     "dbs=%s, users=%s, "
                     "backups=%s, nics=%s, replica_of=%s replica_count=%s, "
                     "configuration=%s, locality=%s, availability_zone=%s, "
                     "region=%s}",
                     context['name'], context['volume'],
                     self._get_volume_type(context), context['flavor'],
                     datastore, datastore_version,
                     self._get_databases(context), self._get_users(context),
                     self._get_backup(context), self._get_nics(context),
                     context.get('master'), context['replica_count'],
                     self._get_config(context), self._get_locality(context),
                     avail_zone, self._get_region(context))
            api.trove.instance_create(request,
                                      context['name'],
                                      context['volume'],
                                      context['flavor'],
                                      datastore=datastore,
                                      datastore_version=datastore_version,
                                      databases=self._get_databases(context),
                                      users=self._get_users(context),
                                      restore_point=self._get_backup(context),
                                      nics=self._get_nics(context),
                                      replica_of=context.get('master'),
                                      replica_count=context['replica_count'],
                                      volume_type=self._get_volume_type(
                                          context),
                                      configuration=self._get_config(context),
                                      locality=self._get_locality(context),
                                      availability_zone=avail_zone,
                                      region_name=self._get_region(context))
            return True
        except Exception:
            exceptions.handle(request)
            return False
