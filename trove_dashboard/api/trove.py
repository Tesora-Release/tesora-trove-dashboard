# Copyright 2013 Rackspace Hosting.
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

from horizon.utils import functions as utils
from horizon.utils.memoized import memoized  # noqa

from mistralclient.api import client as mistral_client

from openstack_auth import utils as auth_utils
from openstack_dashboard.api import base

from troveclient.common import Paginated
from troveclient.v1 import client


LOG = logging.getLogger(__name__)


@memoized
def troveclient(request):
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    trove_url = base.url_for(request, 'database')
    c = client.Client(request.user.username,
                      request.user.token.id,
                      project_id=request.user.project_id,
                      auth_url=trove_url,
                      insecure=insecure,
                      cacert=cacert,
                      http_log_debug=settings.DEBUG)
    c.client.auth_token = request.user.token.id
    c.client.management_url = trove_url
    return c


@memoized
def mistralclient(request):
    auth_url = getattr(settings, 'OPENSTACK_KEYSTONE_URL', None)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    return mistral_client.client(username=request.user.username,
                                 auth_token=request.user.token.id,
                                 project_id=request.user.tenant_id,
                                 auth_url=auth_url,
                                 service_type='workflowv2',
                                 cacert=cacert,
                                 insecure=insecure)


def bucket_create(request, instance_id, name, password, bucket_ramsize=None,
                  bucket_replica=None, enable_index_replica=None,
                  bucket_eviction_policy=None, bucket_priority=None):
    return user_create(request, instance_id, name, password,
                       bucket_ramsize=bucket_ramsize,
                       bucket_replica=bucket_replica,
                       enable_index_replica=enable_index_replica,
                       bucket_eviction_policy=bucket_eviction_policy,
                       bucket_priority=bucket_priority)


def bucket_delete(request, instance_id, name):
    return user_delete(request, instance_id, name)


def bucket_get(request, instance_id, name):
    return user_get(request, instance_id, name)


def bucket_list(request, instance_id):
    return users_list(request, instance_id)


def bucket_update(request, instance_id, name,
                  new_password=None, bucket_ramsize=None, bucket_replica=None,
                  enable_index_replica=None, bucket_eviction_policy=None,
                  bucket_priority=None):
    return user_update_attributes(
        request, instance_id, name, new_password=new_password,
        bucket_ramsize=bucket_ramsize,
        bucket_replica=bucket_replica,
        enable_index_replica=enable_index_replica,
        bucket_eviction_policy=bucket_eviction_policy,
        bucket_priority=bucket_priority)


def cluster_list(request, marker=None):
    page_size = utils.get_page_size(request)
    return troveclient(request).clusters.list(limit=page_size, marker=marker)


def cluster_get(request, cluster_id):
    return troveclient(request).clusters.get(cluster_id)


def cluster_delete(request, cluster_id):
    return troveclient(request).clusters.delete(cluster_id)


def cluster_force_delete(request, cluster_id):
    cluster_reset_status(request, cluster_id, force_delete=True)
    return cluster_delete(request, cluster_id)


def cluster_reset_status(request, cluster_id, force_delete=False):
    return troveclient(request).clusters.reset_status(cluster_id,
                                                      force_delete=(
                                                          force_delete))


def cluster_configuration_attach(request, cluster_id, configuration):
    return troveclient(request).clusters.configuration_attach(
        cluster_id, configuration)


def cluster_configuration_detach(request, cluster_id):
    return troveclient(request).clusters.configuration_detach(cluster_id)


def cluster_create(request, name, volume, flavor, num_instances,
                   datastore, datastore_version,
                   nics=None, root_password=None, locality=None,
                   availability_zone=None, region=None, instance_type=None,
                   extended_properties=None, configuration=None):
    instances = []
    for i in range(num_instances):
        instance = {}
        instance["flavorRef"] = flavor
        if volume > 0:
            instance["volume"] = {'size': volume}
        if nics:
            instance["nics"] = [{'net-id': nics}]
        if availability_zone:
            instance["availability_zone"] = availability_zone
        if region:
            instance["region"] = region
        if instance_type:
            instance["type"] = instance_type
        instances.append(instance)

    # TODO(saurabhs): vertica needs root password on cluster create
    return troveclient(request).clusters.create(
        name,
        datastore,
        datastore_version,
        instances=instances,
        locality=locality,
        extended_properties=extended_properties,
        configuration=configuration
    )


def cluster_grow(request, cluster_id, new_instances):
    instances = []
    for new_instance in new_instances:
        instance = {}
        instance["flavorRef"] = new_instance.flavor_id
        if new_instance.volume > 0:
            instance["volume"] = {'size': new_instance.volume}
        if new_instance.name:
            instance["name"] = new_instance.name
        if new_instance.type:
            instance["type"] = new_instance.type
        if new_instance.related_to:
            instance["related_to"] = new_instance.related_to
        if new_instance.nics:
            instance["nics"] = [{'net-id': new_instance.nics}]
        if new_instance.availability_zone:
            instance["availability_zone"] = new_instance.availability_zone
        if new_instance.region:
            instance["region"] = new_instance.region
        instances.append(instance)
    return troveclient(request).clusters.grow(cluster_id, instances)


def cluster_restart(request, cluster_id):
    return troveclient(request).clusters.restart(cluster_id)


def cluster_shrink(request, cluster_id, instances):
    return troveclient(request).clusters.shrink(cluster_id, instances)


def cluster_upgrade(request, cluster_id, datastore_version):
    return troveclient(request).clusters.upgrade(cluster_id,
                                                 datastore_version)


def create_cluster_root(request, cluster_id, password):
    # It appears the code below depends on this trove change
    # https://review.openstack.org/#/c/166954/.  Comment out when that
    # change merges.
    # return troveclient(request).cluster.reset_root_password(cluster_id)
    troveclient(request).root.create_cluster_root(cluster_id, password)


def instance_list(request, marker=None, include_clustered=False):
    page_size = utils.get_page_size(request)
    return troveclient(request).instances.list(
        limit=page_size, marker=marker, include_clustered=include_clustered)


def instance_list_all(request, include_clustered=False):
    instances = instance_list(request, include_clustered=include_clustered)
    marker = instances.next
    while marker:
        temp_instances = instance_list(request, marker=marker,
                                       include_clustered=include_clustered)
        marker = temp_instances.next
        instances.items += temp_instances.items
        instances.links = temp_instances.links
    instances.next = None
    return instances


def instance_list_master(request, marker=None):
    page_size = utils.get_page_size(request)
    master_instances = []
    new_marker = marker
    while len(master_instances) < page_size:
        instances = instance_list(request, marker=new_marker)
        for instance in instances:
            if hasattr(instance, 'replicas'):
                master_instances.append(instance)
            if len(master_instances) >= page_size:
                break
        if len(master_instances) >= page_size:
            new_marker = instance.id
            break
        new_marker = instances.next
        if not new_marker:
            break

    paginated_instances = Paginated(items=master_instances,
                                    next_marker=new_marker)
    return paginated_instances


def instance_get(request, instance_id):
    return troveclient(request).instances.get(instance_id)


def instance_delete(request, instance_id):
    return troveclient(request).instances.delete(instance_id)


def instance_force_delete(request, instance_id):
    instance_reset_status(request, instance_id, force_delete=True)
    return instance_delete(request, instance_id)


def instance_reset_status(request, instance_id, force_delete=False):
    return troveclient(request).instances.reset_status(instance_id,
                                                       force_delete=(
                                                           force_delete))


def instance_create(request, name, volume, flavor, databases=None,
                    users=None, restore_point=None, nics=None,
                    datastore=None, datastore_version=None,
                    replica_of=None, replica_count=None,
                    volume_type=None, configuration=None,
                    locality=None, availability_zone=None, region_name=None):
    # TODO(dklyle): adding conditional to support trove without volume
    # support for now until API supports checking for volume support
    if volume > 0:
        volume_params = {'size': volume}
        if volume_type:
            volume_params['type'] = volume_type
    else:
        volume_params = None
    return troveclient(request).instances.create(
        name,
        flavor,
        volume=volume_params,
        databases=databases,
        users=users,
        restorePoint=restore_point,
        nics=nics,
        datastore=datastore,
        datastore_version=datastore_version,
        replica_of=replica_of,
        replica_count=replica_count,
        configuration=configuration,
        locality=locality,
        availability_zone=availability_zone,
        region_name=region_name
    )


def instance_resize_volume(request, instance_id, size):
    return troveclient(request).instances.resize_volume(instance_id, size)


def instance_resize(request, instance_id, flavor_id):
    return troveclient(request).instances.resize_instance(instance_id,
                                                          flavor_id)


def instance_backups(request, instance_id):
    return troveclient(request).instances.backups(instance_id)


def instance_restart(request, instance_id):
    return troveclient(request).instances.restart(instance_id)


def instance_upgrade(request, instance_id, datastore_version):
    return troveclient(request).instances.upgrade(instance_id,
                                                  datastore_version)


def instance_detach_replica(request, instance_id):
    return troveclient(request).instances.edit(instance_id,
                                               detach_replica_source=True)


def promote_to_replica_source(request, instance_id):
    return troveclient(request).instances.promote_to_replica_source(
        instance_id)


def eject_replica_source(request, instance_id):
    return troveclient(request).instances.eject_replica_source(instance_id)


def database_list(request, instance_id):
    return troveclient(request).databases.list(instance_id)


def database_create(request, instance_id, db_name, character_set=None,
                    collation=None):
    database = {'name': db_name}
    if collation:
        database['collate'] = collation
    if character_set:
        database['character_set'] = character_set
    return troveclient(request).databases.create(instance_id, [database])


def database_delete(request, instance_id, db_name):
    return troveclient(request).databases.delete(instance_id, db_name)


def backup_list(request, limit=None, marker=None, datastore=None):
    if limit:
        page_size = limit
    else:
        page_size = utils.get_page_size(request)
    return troveclient(request).backups.list(limit=page_size,
                                             marker=marker,
                                             datastore=datastore)


def backup_get(request, backup_id):
    return troveclient(request).backups.get(backup_id)


def backup_delete(request, backup_id):
    return troveclient(request).backups.delete(backup_id)


def backup_create(request, name, instance_id, description=None,
                  parent_id=None):
    return troveclient(request).backups.create(name, instance_id,
                                               description, parent_id)


def flavor_list(request):
    flavors = troveclient(request).flavors.list()
    for flavor in flavors:
        flavor.id = flavor.str_id
    return flavors


def datastore_flavors(request, datastore_name=None,
                      datastore_version=None):
    # if datastore info is available then get datastore specific flavors
    if datastore_name and datastore_version:
        try:
            return troveclient(request).flavors.\
                list_datastore_version_associated_flavors(datastore_name,
                                                          datastore_version)
        except Exception:
            LOG.warning("Failed to retrieve datastore specific flavors")
    return flavor_list(request)


def flavor_get(request, flavor_id):
    return troveclient(request).flavors.get(flavor_id)


def volume_type_list(request):
    return troveclient(request).volume_types.list()


def datastore_volume_types(request, datastore_name=None,
                           datastore_version=None):
    # if datastore info is available then get datastore specific types
    if datastore_name and datastore_version:
        try:
            return troveclient(request).volume_types.\
                list_datastore_version_associated_volume_types(
                    datastore_name, datastore_version)
        except Exception:
            LOG.warn("Failed to retrive datastore specific volume types")
    return volume_type_list(request)


def root_enable(request, instance_ids):
    username, password = troveclient(request).root.create(instance_ids[0])
    return username, password


def root_show(request, instance_id):
    return troveclient(request).root.is_root_enabled(instance_id)


def root_disable(request, instance_id):
    return troveclient(request).root.delete(instance_id)


def users_list(request, instance_id):
    return troveclient(request).users.list(instance_id)


def user_create(request, instance_id, username, password,
                host=None, databases=[], roles=None,
                # couchbase params
                bucket_ramsize=None, bucket_replica=None,
                enable_index_replica=False, bucket_eviction_policy=None,
                bucket_priority=None
                ):
    user = {'name': username, 'password': password, 'databases': databases}
    if host:
        user['host'] = host
    if roles:
        user['roles'] = roles
    if bucket_ramsize:
        user['bucket_ramsize'] = bucket_ramsize
    if bucket_replica:
        user['bucket_replica'] = bucket_replica
    user['enable_index_replica'] = int(enable_index_replica)
    if bucket_eviction_policy:
        user['bucket_eviction_policy'] = bucket_eviction_policy
    if bucket_priority:
        user['bucket_priority'] = bucket_priority

    return troveclient(request).users.create(instance_id, [user])


def user_delete(request, instance_id, user, host=None):
    return troveclient(request).users.delete(instance_id, user, hostname=host)


def user_get(request, instance_id, user_id, host=None):
    return troveclient(request).users.get(instance_id, user_id, hostname=host)


def user_update_attributes(request, instance_id, name, host=None,
                           new_name=None, new_password=None, new_host=None,
                           bucket_ramsize=None, bucket_replica=None,
                           enable_index_replica=False,
                           bucket_eviction_policy=None, bucket_priority=None):
    new_attributes = {}
    if new_name:
        new_attributes['name'] = new_name
    if new_password:
        new_attributes['password'] = new_password
    if new_host:
        new_attributes['host'] = new_host
    if bucket_ramsize:
        new_attributes['bucket_ramsize'] = bucket_ramsize
    if bucket_replica:
        new_attributes['bucket_replica'] = bucket_replica
    new_attributes['enable_index_replica'] = int(enable_index_replica)
    if bucket_eviction_policy:
        new_attributes['bucket_eviction_policy'] = bucket_eviction_policy
    if bucket_priority:
        new_attributes['bucket_priority'] = bucket_priority

    return troveclient(request).users.update_attributes(
        instance_id, name, newuserattr=new_attributes, hostname=host)


def user_list_access(request, instance_id, username, host=None):
    return troveclient(request).users.list_access(
        instance_id, username, hostname=host)


def user_grant_access(request, instance_id, username, databases, host=None):
    return troveclient(request).users.grant(
        instance_id, username, databases, hostname=host)


def user_revoke_access(request, instance_id, username, database, host=None):
    return troveclient(request).users.revoke(
        instance_id, username, database, hostname=host)


def user_show_access(request, instance_id, username, host=None):
    return troveclient(request).users.list_access(
        instance_id, username, hostname=host)


def datastore_list(request):
    return troveclient(request).datastores.list()


def datastore_version_list(request, datastore):
    return troveclient(request).datastore_versions.list(datastore)


def datastore_get(request, datastore_id):
    return troveclient(request).datastores.get(datastore_id)


def instance_attach_configuration(request, instance_id, configuration):
    return troveclient(request).instances.modify(instance_id,
                                                 configuration=configuration)


def instance_detach_configuration(request, instance_id):
    return troveclient(request).instances.modify(instance_id)


def configuration_list(request):
    return troveclient(request).configurations.list()


def configuration_get(request, group_id):
    return troveclient(request).configurations.get(group_id)


def configuration_parameters_list(request, datastore, datastore_version):
    return troveclient(request).configuration_parameters.parameters(
        datastore, datastore_version)


def configuration_create(request,
                         name,
                         values,
                         description=None,
                         datastore=None,
                         datastore_version=None):
    return troveclient(request).configurations.create(name,
                                                      values,
                                                      description,
                                                      datastore,
                                                      datastore_version)


def configuration_delete(request, group_id):
    return troveclient(request).configurations.delete(group_id)


def configuration_instances(request, group_id):
    return troveclient(request).configurations.instances(group_id)


def configuration_update(request, group_id, values):
    return troveclient(request).configurations.update(group_id, values)


def configuration_default(request, instance_id):
    return troveclient(request).instances.configuration(instance_id)


def log_list(request, instance_id):
    return troveclient(request).instances.log_list(instance_id)


def log_enable(request, instance_id, log_name):
    return troveclient(request).instances.log_enable(instance_id, log_name)


def log_disable(request, instance_id, log_name):
    return troveclient(request).instances.log_disable(instance_id, log_name)


def log_publish(request, instance_id, log_name):
    return troveclient(request).instances.log_publish(instance_id, log_name)


def log_discard(request, instance_id, log_name):
    return troveclient(request).instances.log_discard(instance_id, log_name)


def log_tail(request, instance_id, log_name, publish, lines, swift=None):
    return troveclient(request).instances.log_generator(instance_id,
                                                        log_name,
                                                        publish=publish,
                                                        lines=lines,
                                                        swift=swift)


def region_list(request):
    return auth_utils.get_user(request).available_services_regions


def execution_delete(request, execution, mistral_client=None):
    return troveclient(request).backups.execution_delete(
        execution, mistral_client=mistral_client)


def execution_list(request, schedule, mistral_client=None, marker=''):
    if marker is None:
        marker = ''
    page_size = utils.get_page_size(request)
    executions = list(troveclient(request).backups.execution_list(
        schedule, mistral_client=mistral_client,
        limit=page_size + 1, marker=marker))

    has_more_data = False
    if len(executions) > page_size:
        executions.pop(-1)
        has_more_data = True
    elif len(executions) == getattr(settings, 'API_RESULT_LIMIT',
                                              1000):
        has_more_data = True
    return (executions, has_more_data)


def schedule_create(request, instance, pattern, name, description=None,
                    mistral_client=None, incremental=False):
    return troveclient(request).backups.schedule_create(
        instance, pattern, name, description=description,
        mistral_client=mistral_client, incremental=incremental)


def schedule_delete(request, schedule, mistral_client=None):
    return troveclient(request).backups.schedule_delete(
        schedule, mistral_client=mistral_client)


def schedule_list(request, instance, mistral_client=None):
    return troveclient(request).backups.schedule_list(
        instance, mistral_client=mistral_client)


def schedule_show(request, schedule, mistral_client=None):
    return troveclient(request).backups.schedule_show(
        schedule, mistral_client=mistral_client)
