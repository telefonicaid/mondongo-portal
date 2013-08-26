# Copyright 2013 Telefonica Investigación y Desarrollo, S.A.U
#
# This file is part of Mondongo Portal
#
# Mondongo Portal is free software: you can redistribute it and/or modify it under the terms
# of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Mondongo Portal is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License along with Mondongo Portal. If not,
# see http://www.gnu.org/licenses/.
#
# For those usages not covered by the GNU Affero General Public License please contact with fermin at tid dot es

__author__ = 'fermin'

from time import sleep
from mondongo.models import Configuration
import json
import logging
from requests import request

#logger = logging.getLogger(__name__)
logger = logging.getLogger("mondongo_logger")

POLL_INTERVAL = 5

def get_cluster_info():

    # We apply to filters to the list of the user: one by a given dataset, the other by tag (looking for
    # mondongo=true)

    # FIXME: move conf to a global variable
    conf = Configuration.objects.all()[0]

    result = _do_request('GET', conf.api_endpoint + conf.api_user + '/machines?dataset=' + conf.mongo_dataset)

    filtered_list = []
    for vm in result:
        if _check_mondongo_tag_in_vm(vm['id']):
            filtered_list.append(vm)

    return filtered_list


def get_vm_status(vm_id):

    # FIXME: move conf to a global variable
    conf = Configuration.objects.all()[0]

    result = _do_request('GET', conf.api_endpoint + conf.api_user + '/machines/' + vm_id)
    return result['state']


def get_vm_credentials(vm_id):

    # FIXME: move conf to a global variable
    conf = Configuration.objects.all()[0]

    result = _do_request('GET', conf.api_endpoint + conf.api_user + '/machines/' + vm_id + '/metadata?credentials=true')
    return result['credentials']


def stop_vm(vm_id):

    # FIXME: move conf to a global variable
    conf = Configuration.objects.all()[0]

    # As safe measure, we check that the VM belong to dataset and has the the mondongo=true tag
    _do_request('POST', conf.api_endpoint + conf.api_user + '/machines/' + vm_id + '?action=stop')


def destroy_vm(vm_id):

    # FIXME: move conf to a global variable
    conf = Configuration.objects.all()[0]

    # As safe measure, we check that the VM belong to dataset and has the the mondongo=true tag
    result = _do_request('GET', conf.api_endpoint + conf.api_user + '/machines/' + vm_id)
    if result['dataset'] != conf.mongo_dataset:
        return False

    if not _check_mondongo_tag_in_vm(vm_id):
        return False

    # This method assumes that the VM is previously stoped, otherwise the destroy operation will fail
    # accordingly Joyent documentation
    _do_request('DELETE', conf.api_endpoint + conf.api_user + '/machines/' + vm_id)

    return True


def create_vm(id_shard, id_replica_set, init_script, wait_ready=False):

    # FIXME: move conf to a global variable
    conf = Configuration.objects.all()[0]

    input_data = {
        'name': 'mondongo' + str(id_shard) + str(id_replica_set),
        'package': conf.mongo_package,
        'dataset': conf.mongo_dataset,
        'tag.mondongo': 'true',
        'metadata.user-script': init_script,
    }

    vm = _do_request('POST', conf.api_endpoint + conf.api_user + '/machines', data=json.dumps(input_data))

    # If wait_ready=True, we don't return until the VM is up and running
    if wait_ready:
        state = get_vm_status(vm['id'])
        while state != 'running':
            sleep(POLL_INTERVAL)
            state = get_vm_status(vm['id'])

    return vm


##########
# Helpers
##########

def _check_mondongo_tag_in_vm(vm_id):

    # FIXME: move conf to a global variable
    conf = Configuration.objects.all()[0]

    result = _do_request('GET', conf.api_endpoint + conf.api_user + '/machines/' + vm_id + '/tags')
    return result.get('mondongo') and result['mondongo'] == 'true'


def _do_request(verb, url, data=None):

    logger.info('--> ' + verb + ' ' + url)
    response = request(verb, url, headers=_base_headers(), data=data, verify=False)
    logger.info('<-- ' + str(response.status_code))
    logger.info('<-- [' + str(response.text) + ']')
    if (len(str(response.text)) != 0):
        return response.json()



def _base_headers():
    # FIXME: move conf to a global variable
    conf = Configuration.objects.all()[0]
    return {'Content-Type': 'application/json',
            'Authorization': conf.authorization_token,
            'X-Api-Version': conf.version_token}
