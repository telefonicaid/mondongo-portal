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

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from rest_request import get_cluster_info, stop_vm, destroy_vm, get_vm_status, create_vm, get_vm_credentials
from time import sleep
from scripts import script_master, script_slave, script_mongos, script_config_server

POLL_INTERVAL = 5

@login_required
def view(request):
    view_params = {'user': request.user.username}
    view_params['results'] = []

    # We pass to the view a list of list, because we need the parameters in order, acording to the
    # <table> in the view template
    for vm in get_cluster_info():
        credentials = get_vm_credentials(vm['id'])
        entry = []
        entry.append(vm['name'])
        entry.append(vm['state'])
        entry.append(vm['primaryIp'])
        entry.append(vm['memory'])
        entry.append(vm['disk'])
        entry.append(credentials['root'])
        entry.append(credentials['admin'])
        entry.append(vm['created'])
        view_params['results'].append(entry)

    return render_to_response('mondongo/view.html', view_params, context_instance=RequestContext(request))


@login_required
def create_form(request):
    view_params = {'user': request.user.username}
    return render_to_response('mondongo/create_form.html', view_params, context_instance=RequestContext(request))


@login_required
def create(request):
    view_params = {'user': request.user.username}

    if request.POST.get('replica_set') and request.POST['replica_set'] == 'true':
        view_params['error_message'] = "Replica set option is not (yet) supported"
        return render_to_response('mondongo/create_result.html', view_params)

    view_params['shard_instances'] = int(request.POST['shard_instances'])
    view_params['n_shards'] = int(request.POST['n_shards'])
    view_params['total'] = int(request.POST['n_shards']) * int(request.POST['shard_instances'])

    ip_shards = []
    for i in range(view_params['n_shards']):
        # The first VM acts as master
        vm = create_vm(i, 0, script_master())
        ip_master = vm['primaryIp']
        # We add the IP of the master to the ip_shards array just in casse we need it
        ip_shards.append(ip_master)
        for j in range(1, int(view_params['shard_instances'])):
            create_vm(i, j, script_slave(ip_master))

    # If more than a shard exist, then we create an addition VM to host the mongos process and
    # additional VM to host the config server. Why not using the same VM for mongos and config
    # server? Because in that case we will have the "can't use localhost as a shard since all shards
    # need to communicate. either use all shards and configdbs in localhost or all in actual IPs" error
    if int(view_params['n_shards']) > 1:
        vm = create_vm('C', 'C', script_config_server())
        create_vm('S', 'S', script_mongos(ip_shards, vm['primaryIp'], request.POST['shard_db'],
                  request.POST['shard_col'], request.POST['shard_key']))
        view_params['total'] += 2

    return render_to_response('mondongo/create_result.html', view_params, context_instance=RequestContext(request))


@login_required
def destroy(request):
    view_params = {'user': request.user.username}

    for vm in get_cluster_info():
        state = vm['state']
        if state != 'stopped':
            stop_vm(vm['id'])
        while state != 'stopped':
            sleep(POLL_INTERVAL)
            state = get_vm_status(vm['id'])
        destroy_vm(vm['id'])

    return render_to_response('mondongo/destroy_result.html', view_params, context_instance=RequestContext(request))
