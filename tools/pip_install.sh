#!/bin/sh

BRANCH_NAME=${BRANCH_NAME:-dev/EE-1.9}
BRANCH_NAME=${ZUUL_BRANCH:-$BRANCH_NAME}

set -e

install_cmd="pip install"
uninstall_cmd="pip uninstall -y"

# install all pip libraries from pypi first
$install_cmd -U $*

# remove the horizon installed from source (can't get rid of it in test-requirements.txt due to global requirements conflict
$uninstall_cmd horizon

# TODO: replace the hardcoded branch with env variable
HORIZON_PIP_LOCATION="git://github.com/openstack/horizon.git@stable/mitaka#egg=horizon"
$install_cmd -U -e ${HORIZON_PIP_LOCATION}

# remove the python-troveclient from pypi
$uninstall_cmd python-troveclient

# install python-troveclient from source
PYTHON_TROVECLIENT_PIP_LOCATION="git://github.com/Tesora/tesora-python-troveclient.git@$BRANCH_NAME#egg=python-troveclient"
$install_cmd -U -e ${PYTHON_TROVECLIENT_PIP_LOCATION}

PYTHON_MISTRALCLIENT_PIP_LOCATION="git://github.com/Tesora/tesora-python-mistralclient.git@$BRANCH_NAME#egg=python-mistralclient"
$install_cmd -U -e ${PYTHON_MISTRALCLIENT_PIP_LOCATION}

exit $?
