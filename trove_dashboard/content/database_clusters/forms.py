# Copyright 2015 HP Software, LLC
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import uuid

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import memoized
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils

from trove_dashboard import api as trove_api
from trove_dashboard.content.database_clusters \
    import cluster_manager
from trove_dashboard.content.databases import db_capability
from trove_dashboard.content import utils

LOG = logging.getLogger(__name__)


class LaunchForm(forms.SelfHandlingForm):
    availability_zone = forms.ChoiceField(
        label=_("Availability Zone"),
        required=False)
    name = forms.CharField(label=_("Cluster Name"),
                           max_length=80)
    datastore = forms.ChoiceField(
        label=_("Datastore"),
        help_text=_("Type and version of datastore."),
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'datastore'
        }))
    volume = forms.IntegerField(
        label=_("Volume Size"),
        min_value=0,
        initial=getattr(settings, "TROVE_DEFAULT_CLUSTER_VOL_SIZE", 1),
        help_text=_("Size of the volume in GB."))
    region = forms.ChoiceField(
        label=_("Region"),
        required=False)
    locality = forms.ChoiceField(
        label=_("Locality"),
        choices=[("", "None"),
                 ("affinity", "affinity"),
                 ("anti-affinity", "anti-affinity")],
        required=False,
        help_text=_("Specify whether instances in the cluster will "
                    "be created on the same hypervisor (affinity) or on "
                    "different hypervisors (anti-affinity)."))
    instance_type = forms.CharField(
        label=_("Type"),
        required=False,
        help_text=_("Cluster node type"))
    root_password = forms.CharField(
        label=_("Root Password"),
        required=False,
        help_text=_("Password for root user."),
        widget=forms.PasswordInput(attrs={
            'class': 'switched',
            'data-switch-on': 'datastore',
        }))
    num_instances_vertica = forms.IntegerField(
        label=_("Number of Instances"),
        min_value=3,
        initial=3,
        required=False,
        help_text=_("Number of instances in the cluster. (Read only)"),
        widget=forms.TextInput(attrs={
            'readonly': 'readonly',
            'class': 'switched',
            'data-switch-on': 'datastore',
        }))
    num_shards = forms.IntegerField(
        label=_("Number of Shards"),
        min_value=1,
        initial=1,
        required=False,
        help_text=_("Number of shards. (Read only)"),
        widget=forms.TextInput(attrs={
            'readonly': 'readonly',
            'class': 'switched',
            'data-switch-on': 'datastore',
        }))
    num_instances = forms.IntegerField(
        label=_("Number of Instances"),
        initial=3,
        required=False,
        help_text=_("Number of instances in the cluster."),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'datastore',
        }))
    oracle_rac_database = forms.CharField(
        label=_("Database"),
        required=False,
        help_text=_("Specify the name of the initial database."),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'datastore',
        }))
    oracle_rac_subnet = forms.CharField(
        label=_("Subnet"),
        required=False,
        help_text=_("Subnet of the cluster."),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'datastore',
        }))
    oracle_rac_storage_type = forms.CharField(
        label=_("Storage Type"),
        initial='nfs',
        required=False,
        help_text=_("Storage type of cluster. (Read only)"),
        widget=forms.TextInput(attrs={
            'readonly': 'readonly',
            'class': 'switched',
            'data-switch-on': 'datastore',
        }))
    oracle_rac_votedisk_mount = forms.CharField(
        label=_("Voting Files Disk Mount"),
        required=False,
        help_text=_("Specify the voting files disk mount."),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'datastore',
        }))
    oracle_rac_registry_mount = forms.CharField(
        label=_("Registry Mount"),
        required=False,
        help_text=_("Specify the registry mount."),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'datastore',
        }))
    oracle_rac_database_mount = forms.CharField(
        label=_("Database Mount"),
        required=False,
        help_text=_("Specify the database mount."),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'datastore',
        }))

    # (name of field variable, label)
    default_fields = [
        ('num_instances', _('Number of Instances'))
    ]
    mongodb_fields = default_fields + [
        ('num_shards', _('Number of Shards')),
    ]
    oracle_rac_fields = default_fields + [
        ('oracle_rac_database', _('Database')),
        ('oracle_rac_subnet', _('Subnet')),
        ('oracle_rac_storage_type', _('Storage Type')),
        ('oracle_rac_votedisk_mount', _('Voting Files Disk Mount')),
        ('oracle_rac_registry_mount', _('Registry Mount')),
        ('oracle_rac_database_mount', _('Database Mount'))
    ]
    vertica_fields = [
        ('num_instances_vertica', ('Number of Instances')),
        ('root_password', _('Root Password')),
    ]

    def __init__(self, request, *args, **kwargs):
        super(LaunchForm, self).__init__(request, *args, **kwargs)

        self.fields['datastore'].choices = self.populate_datastore_choices(
            request)
        self.fields['availability_zone'].choices = (
            self.populate_availability_zone_choices(request))
        self.fields['region'].choices = self.populate_region_choices(
            request)
        if not getattr(settings, 'DATABASE_ENABLE_REGION_SUPPORT', False):
            self.fields['region'].widget = forms.HiddenInput()

    def clean(self):
        datastore_field_value = self.data.get("datastore", None)
        if datastore_field_value:
            datastore, datastore_version = (
                utils.parse_datastore_and_version_text(datastore_field_value))

            flavor_field_name = utils.build_widget_field_name(
                datastore, datastore_version)
            if not self.data.get(flavor_field_name, None):
                msg = _("The flavor must be specified.")
                self._errors[flavor_field_name] = self.error_class([msg])

            if db_capability.is_vertica_datastore(datastore):
                if not self.data.get("root_password", None):
                    msg = _("Password for root user must be specified.")
                    self._errors["root_password"] = self.error_class([msg])
            else:
                if int(self.data.get("num_instances", 0)) < 1:
                    msg = _("The number of instances must be greater than 1.")
                    self._errors["num_instances"] = self.error_class([msg])

                if db_capability.is_mongodb_datastore(datastore):
                    if int(self.data.get("num_shards", 0)) < 1:
                        msg = _("The number of shards must be greater than 1.")
                        self._errors["num_shards"] = self.error_class([msg])

                if db_capability.is_oracle_rac_datastore(datastore):
                    if not self.data.get("oracle_rac_database", None):
                        msg = _("Database must be specified.")
                        self._errors["oracle_rac_database"] = (
                            self.error_class([msg])
                        )
                    if not self.data.get("oracle_rac_subnet", None):
                        msg = _("Subnet must be specified.")
                        self._errors["oracle_rac_subnet"] = (
                            self.error_class([msg])
                        )
                    if not self.data.get("oracle_rac_votedisk_mount", None):
                        msg = _("Voting Files Disk Mount must be specified.")
                        self._errors["oracle_rac_votedisk_mount"] = (
                            self.error_class([msg])
                        )
                    if not self.data.get("oracle_rac_registry_mount", None):
                        msg = _("Registry mount must be specified.")
                        self._errors["oracle_rac_registry_mount"] = (
                            self.error_class([msg])
                        )
                    if not self.data.get("oracle_rac_database_mount", None):
                        msg = _("Database mount must be specified.")
                        self._errors["oracle_rac_database_mount"] = (
                            self.error_class([msg])
                        )

        if not self.data.get("locality", None):
            self.cleaned_data["locality"] = None

        if not self.data.get("region", None):
            self.cleaned_data["region"] = None

        return self.cleaned_data

    @memoized.memoized_method
    def datastore_flavors(self, request, datastore_name, datastore_version):
        try:
            return trove_api.trove.datastore_flavors(
                request, datastore_name, datastore_version)
        except Exception:
            LOG.exception("Exception while obtaining flavors list")
            self._flavors = []
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(request,
                              _('Unable to obtain flavors.'),
                              redirect=redirect)

    @memoized.memoized_method
    def populate_network_choices(self, request, datastore, datastore_version):
        network_list = []
        try:
            tenant_id = self.request.user.tenant_id
            networks = api.neutron.network_list_for_tenant(request,
                                                           tenant_id)
            network_list = [(network.id, network.name_or_id)
                            for network in networks]
            if db_capability.is_oracle_rac_datastore(datastore):
                network_list.insert(0, (None, None))
        except exceptions.ServiceCatalogException:
            network_list = []
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(request,
                              _('Unable to retrieve networks.'),
                              redirect=redirect)
        return network_list

    @memoized.memoized_method
    def populate_availability_zone_choices(self, request):
        try:
            zones = api.nova.availability_zone_list(request)
        except Exception:
            zones = []
            redirect = reverse('horizon:project:database_clusters:index')
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
    def populate_region_choices(self, request):
        try:
            regions = trove_api.trove.region_list(request)
        except Exception:
            regions = []
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(request,
                              _('Unable to retrieve region list.'),
                              redirect=redirect)
        available_regions = [(region, region) for region in regions]
        if not available_regions:
            available_regions.insert(0, ("", _("No regions found")))
        elif len(available_regions) > 1:
            available_regions.insert(0, ("", _("Default region")))
        return available_regions

    @memoized.memoized_method
    def datastores(self, request):
        try:
            return trove_api.trove.datastore_list(request)
        except Exception:
            LOG.exception("Exception while obtaining datastores list")
            self._datastores = []
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(request,
                              _('Unable to obtain datastores.'),
                              redirect=redirect)

    def filter_cluster_datastores(self, request):
        datastores = []
        for ds in self.datastores(request):
            # TODO(michayu): until capabilities lands
            if db_capability.is_cluster_capable_datastore(ds.name):
                datastores.append(ds)
        return datastores

    @memoized.memoized_method
    def datastore_versions(self, request, datastore):
        try:
            return trove_api.trove.datastore_version_list(request, datastore)
        except Exception:
            LOG.exception("Exception while obtaining datastore version list")
            self._datastore_versions = []
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(request,
                              _('Unable to obtain datastore versions.'),
                              redirect=redirect)

    @memoized.memoized_method
    def populate_config_choices(self, request, datastore, datastore_version):
        try:
            configs = trove_api.trove.configuration_list(request)
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

    def populate_datastore_choices(self, request):
        choices = ()
        datastores = self.filter_cluster_datastores(request)
        if datastores is not None:
            datastore_flavor_fields = {}
            for ds in datastores:
                versions = self.datastore_versions(request, ds.name)
                if versions:
                    # only add to choices if datastore has at least one version
                    version_choices = ()
                    for v in versions:
                        if hasattr(v, 'active') and not v.active:
                            continue
                        selection_text = utils.build_datastore_display_text(
                            ds.name, v.name)
                        widget_text = utils.build_widget_field_name(
                            ds.name, v.name)
                        version_choices = (version_choices +
                                           ((widget_text, selection_text),))
                        self._add_datastore_network_field(request, ds.name,
                                                          v.name)
                        if db_capability.supports_configuration(ds.name):
                            self._add_datastore_config_field(request, ds.name,
                                                             v.name)
                        k, v = self._add_datastore_flavor_field(request,
                                                                ds.name,
                                                                v.name)
                        datastore_flavor_fields[k] = v
                        self._add_attr_to_optional_fields(ds.name,
                                                          widget_text)

                    choices = choices + version_choices
            self._insert_datastore_version_fields(datastore_flavor_fields)
        return choices

    def _add_datastore_flavor_field(self,
                                    request,
                                    datastore,
                                    datastore_version):
        name = utils.build_widget_field_name(datastore, datastore_version)
        attr_key = 'data-datastore-' + name
        field = forms.ChoiceField(
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
            field.choices = instance_utils.sort_flavor_list(
                request, valid_flavors)

        return name, field

    def _add_datastore_network_field(self,
                                     request,
                                     datastore,
                                     datastore_version):
        name = utils.build_widget_field_name(datastore, datastore_version)
        attr_key = 'data-datastore-' + name
        field_name = utils.build_network_field_name(datastore,
                                                    datastore_version)
        self.fields[field_name] = forms.ChoiceField(
            label=_("Network"),
            help_text=_("Network attached to instance"),
            required=False,
            widget=forms.Select(attrs={
                'class': 'switched',
                'data-switch-on': 'datastore',
                attr_key: _("Network")
            }))
        if api.base.is_service_enabled(request, 'network'):
            self.fields[field_name].choices = self.populate_network_choices(
                request, datastore, datastore_version)
        else:
            self.fields[field_name].widget = forms.HiddenInput()

    def _add_datastore_config_field(self,
                                    request,
                                    datastore,
                                    datastore_version):
        name = utils.build_widget_field_name(datastore, datastore_version)
        attr_key = 'data-datastore-' + name
        field_name = utils.build_config_field_name(datastore,
                                                   datastore_version)
        self.fields[field_name] = forms.ChoiceField(
            label=_("Configuration Group"),
            required=False,
            help_text=_("Select a configuration group"),
            widget=forms.Select(attrs={
                'class': 'switched',
                'data-switch-on': 'datastore',
                attr_key: _("Configuration Group")
            }))
        self.fields[field_name].choices = self.populate_config_choices(
            request, datastore, datastore_version)

    def _insert_datastore_version_fields(self, datastore_flavor_fields):
        datastore_index = None
        reordered_fields = self.fields.items()
        for tup in reordered_fields:
            if tup[0] == 'datastore':
                datastore_index = reordered_fields.index(tup)
                break

        for k, v in datastore_flavor_fields.iteritems():
            reordered_fields.insert(datastore_index + 1, (k, v))

        self.fields.clear()
        for tup in reordered_fields:
            self.fields[tup[0]] = tup[1]

    def _add_attr_to_optional_fields(self, datastore, selection_text):
        if db_capability.is_mongodb_datastore(datastore):
            fields = self.mongodb_fields
        elif db_capability.is_vertica_datastore(datastore):
            fields = self.vertica_fields
        elif db_capability.is_oracle_rac_datastore(datastore):
            fields = self.oracle_rac_fields
        else:
            fields = self.default_fields

        for field in fields:
            attr_key = 'data-datastore-' + selection_text
            widget = self.fields[field[0]].widget
            if attr_key not in widget.attrs:
                widget.attrs[attr_key] = field[1]

    def _get_locality(self, data):
        locality = None
        if data.get('locality'):
            locality = data['locality']
        return locality

    def _get_region(self, data):
        region = None
        if data.get('region'):
            region = data['region']
        return region

    def _get_instance_type(self, data):
        instance_type = None
        if data.get('instance_type'):
            instance_type = data['instance_type'].strip().split(",")
        return instance_type

    def _get_configuration(self, data, datastore, datastore_version):
        configuration = None
        config_field_name = utils.build_config_field_name(
            datastore, datastore_version)
        if data.get(config_field_name):
            configuration = data[config_field_name]
        return configuration

    def _get_network(self, data, datastore, datastore_version):
        network = None
        network_field_name = utils.build_network_field_name(datastore,
                                                            datastore_version)
        if data.get(network_field_name):
            network = data[network_field_name]
        return network

    def _build_extended_properties(self, data, datastore):
        extended_properties = None

        if db_capability.is_oracle_rac_datastore(datastore):
            extended_properties = {}
            extended_properties['database'] = data['oracle_rac_database']
            extended_properties['votedisk_mount'] = (
                data['oracle_rac_votedisk_mount']
            )
            extended_properties['registry_mount'] = (
                data['oracle_rac_registry_mount']
            )
            extended_properties['database_mount'] = (
                data['oracle_rac_database_mount']
            )
            extended_properties['subnet'] = data['oracle_rac_subnet']
            extended_properties['storage_type'] = (
                data['oracle_rac_storage_type']
            )

        return extended_properties

    @sensitive_variables('data')
    def handle(self, request, data):
        try:
            avail_zone = data.get('availability_zone', None)
            datastore, datastore_version = (
                utils.parse_datastore_and_version_text(data['datastore']))

            flavor_field_name = utils.build_widget_field_name(
                datastore, datastore_version)
            flavor = data[flavor_field_name]
            num_instances = data['num_instances']
            root_password = None
            if db_capability.is_vertica_datastore(datastore):
                root_password = data['root_password']
                num_instances = data['num_instances_vertica']
            extended_properties = self._build_extended_properties(data,
                                                                  datastore)
            LOG.info("Launching cluster with parameters "
                     "{name=%s, volume=%s, flavor=%s, "
                     "datastore=%s, datastore_version=%s,"
                     "locality=%s, AZ=%s, region=%s, instance_type=%s,"
                     "configuration=%s",
                     data['name'], data['volume'], flavor,
                     datastore, datastore_version, self._get_locality(data),
                     avail_zone, self._get_region(data),
                     self._get_instance_type(data),
                     self._get_configuration(data, datastore, datastore_version
                                             ))

            trove_api.trove.cluster_create(request,
                                           data['name'],
                                           data['volume'],
                                           flavor,
                                           num_instances,
                                           datastore=datastore,
                                           datastore_version=datastore_version,
                                           nics=(
                                               self._get_network(
                                                   data, datastore,
                                                   datastore_version)),
                                           root_password=root_password,
                                           locality=self._get_locality(data),
                                           availability_zone=avail_zone,
                                           region=self._get_region(data),
                                           instance_type=(
                                               self._get_instance_type(data)),
                                           extended_properties=(
                                               extended_properties),
                                           configuration=(
                                               self._get_configuration(
                                                   data, datastore,
                                                   datastore_version)
                                           ))
            messages.success(request,
                             _('Launched cluster "%s"') % data['name'])
            return True
        except Exception as e:
            redirect = reverse("horizon:project:database_clusters:index")
            exceptions.handle(request,
                              _('Unable to launch cluster. %s') % e.message,
                              redirect=redirect)


class ClusterAddInstanceForm(forms.SelfHandlingForm):
    cluster_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput())
    availability_zone = forms.ChoiceField(
        label=_("Availability Zone"),
        required=False)
    flavor = forms.ChoiceField(
        label=_("Flavor"),
        help_text=_("Size of image to launch."))
    volume = forms.IntegerField(
        label=_("Volume Size"),
        min_value=0,
        initial=1,
        help_text=_("Size of the volume in GB."))
    name = forms.CharField(
        label=_("Name"),
        required=False,
        help_text=_("Optional name of the instance."))
    type = forms.CharField(
        label=_("Instance Type"),
        required=False,
        help_text=_("Optional datastore specific type of the instance."))
    related_to = forms.CharField(
        label=_("Related To"),
        required=False,
        help_text=_("Optional datastore specific value that defines the "
                    "relationship from one instance in the cluster to "
                    "another."))
    network = forms.ChoiceField(
        label=_("Network"),
        help_text=_("Network attached to instance."),
        required=False)
    region = forms.ChoiceField(
        label=_("Region"),
        required=False)

    def __init__(self, request, *args, **kwargs):
        super(ClusterAddInstanceForm, self).__init__(request, *args, **kwargs)
        self.fields['cluster_id'].initial = kwargs['initial']['cluster_id']
        self.fields['flavor'].choices = self.populate_flavor_choices(request)
        self.fields['network'].choices = self.populate_network_choices(
            request)
        self.fields['availability_zone'].choices = (
            self.populate_availability_zone_choices(request))
        self.fields['region'].choices = self.populate_region_choices(request)
        if not getattr(settings, 'DATABASE_ENABLE_REGION_SUPPORT', False):
            self.fields['region'].widget = forms.HiddenInput()

    @memoized.memoized_method
    def flavors(self, request):
        try:
            datastore = None
            datastore_version = None
            datastore_dict = self.initial.get('datastore', None)
            if datastore_dict:
                datastore = datastore_dict.get('type', None)
                datastore_version = datastore_dict.get('version', None)
            return trove_api.trove.datastore_flavors(
                request,
                datastore_name=datastore,
                datastore_version=datastore_version)
        except Exception:
            LOG.exception("Exception while obtaining flavors list")
            self._flavors = []
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(request,
                              _('Unable to obtain flavors.'),
                              redirect=redirect)

    def populate_flavor_choices(self, request):
        flavor_list = [(f.id, "%s" % f.name) for f in self.flavors(request)]
        return sorted(flavor_list)

    @memoized.memoized_method
    def populate_network_choices(self, request):
        network_list = []
        try:
            if api.base.is_service_enabled(request, 'network'):
                tenant_id = self.request.user.tenant_id
                networks = api.neutron.network_list_for_tenant(request,
                                                               tenant_id)
                network_list = [(network.id, network.name_or_id)
                                for network in networks]
            else:
                self.fields['network'].widget = forms.HiddenInput()
        except exceptions.ServiceCatalogException:
            network_list = []
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(request,
                              _('Unable to retrieve networks.'),
                              redirect=redirect)
        return network_list

    @memoized.memoized_method
    def populate_availability_zone_choices(self, request):
        try:
            zones = api.nova.availability_zone_list(request)
        except Exception:
            zones = []
            redirect = reverse('horizon:project:database_clusters:index')
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
    def populate_region_choices(self, request):
        try:
            regions = trove_api.trove.region_list(request)
        except Exception:
            regions = []
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(request,
                              _('Unable to retrieve region list.'),
                              redirect=redirect)
        available_regions = [(region, region) for region in regions]
        if not available_regions:
            available_regions.insert(0, ("", _("No regions found")))
        elif len(available_regions) > 1:
            available_regions.insert(0, ("", _("Default region")))
        return available_regions

    def handle(self, request, data):
        try:
            flavor = trove_api.trove.flavor_get(request, data['flavor'])
            manager = cluster_manager.get(data['cluster_id'])
            manager.add_instance(str(uuid.uuid4()),
                                 data.get('name', None),
                                 data['flavor'],
                                 flavor.name,
                                 data['volume'],
                                 data.get('type', None),
                                 data.get('related_to', None),
                                 data.get('network', None),
                                 data.get('availability_zone', None),
                                 data.get('region', None))
        except Exception as e:
            redirect = reverse("horizon:project:database_clusters:index")
            exceptions.handle(request,
                              _('Unable to grow cluster. %s') % e.message,
                              redirect=redirect)
        return True


class ResetPasswordForm(forms.SelfHandlingForm):
    cluster_id = forms.CharField(widget=forms.HiddenInput())
    password = forms.CharField(widget=forms.PasswordInput(),
                               label=_("New Password"),
                               required=True,
                               help_text=_("New password for cluster access."))

    @sensitive_variables('data')
    def handle(self, request, data):
        password = data.get("password")
        cluster_id = data.get("cluster_id")
        try:
            trove_api.trove.create_cluster_root(request,
                                                cluster_id,
                                                password)
            messages.success(request, _('Root password updated for '
                                        'cluster "%s"') % cluster_id)
        except Exception as e:
            redirect = reverse("horizon:project:database_clusters:index")
            exceptions.handle(request, _('Unable to reset password. %s') %
                              e.message, redirect=redirect)
        return True
