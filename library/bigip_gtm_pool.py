#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Michael Perzel
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: bigip_gtm_pool
short_description: "Manages F5 BIG-IP GTM pools"
description:
    - "Manages F5 BIG-IP GTM pools"
version_added: "2.0"
author: 'Michael Perzel'
notes:
    - "Requires BIG-IP software version >= 11.4"
    - "F5 developed module 'bigsuds' required (see http://devcentral.f5.com)"
    - "Best run as a local_action in your playbook"
    - "Tested with manager and above account privilege level"

requirements:
    - bigsuds
options:
    server:
        description:
            - BIG-IP host
        required: true
    user:
        description:
            - BIG-IP username
        required: true
    password:
        description:
            - BIG-IP password
        required: true
    state:
        description:
            - Pool member state
        required: true
        choices: ['present', 'absent', 'enabled', 'disabled']
    pool:
        description:
            - Pool name
        required: true
    partition:
        description:
            - Partition name
        required: false
        default: Common
'''

EXAMPLES = '''
  - name: Disable pool
    local_action: >
      bigip_gtm_pool
      server=192.168.0.1
      user=admin
      password=mysecret
      state=disabled
      pool=my_pool
      partition=Common
'''
try:
    import bigsuds
except ImportError:
    bigsuds_found = False
else:
    bigsuds_found = True

def bigip_api(server, user, password):
    api = bigsuds.BIGIP(hostname=server, username=user, password=password)
    return api

def get_pools(api):
    try:
        return api.GlobalLB.PoolV2.get_list()
    except Exception, e:
        module.fail_json(msg="received exception: %s" % e)

def get_all_pool_status(api):
    try:
        pool = api.GlobalLB.PoolV2.get_list()
        return pool, api.GlobalLB.PoolV2.get_object_status(pool)
    except Exception, e:
        module.fail_json(msg="received exception: %s" % e)

def get_pool_status(api, pool):
    try:
        return api.GlobalLB.PoolV2.get_object_status([pool])
    except Exception, e:
        module.fail_json(msg="received exception: %s" % e)

def get_pool_state(api, pool):
    state = api.GlobalLB.PoolV2.get_enabled_state([pool])
    state = state[0].split('STATE_')[1].lower()
    return state

def get_pool_statistics(api, pool):
    statistics = api.GlobalLB.PoolV2.get_statistics([pool])
    return statistics

def set_pool_state(api, pool, state):
    state = "STATE_%s" % state.strip().upper()
    api.GlobalLB.PoolV2.set_enabled_state([pool], [state])

def pool_exists(api, pool):
    # hack to determine if pool exists
    result = False
    try:
        api.GlobalLB.PoolV2.get_object_status(pools=[pool])
        result = True
    except bigsuds.OperationFailed, e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result

def member_exists(api, pool, name, server):
    # hack to determine if member exists
    result = False
    try:
        members = [{'name': name, 'server': server}]
        api.GlobalLB.PoolV2.get_member_object_status(pools=[pool], members=[members])
        result = True
    except bigsuds.OperationFailed, e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result

def add_pool_member(api, pool, name, server):
    members = [{'name': name, 'server': server}]
    api.GlobalLB.PoolV2.add_member(pools=[pool], members=[members])

def remove_pool_member(api, pool, name, server):
    members = [{'name': name, 'server': server}]
    api.GlobalLB.PoolV2.remove_member(pools=[pool], members=[members])

def add_pool(api, pool, lb_method):
    lb_method = "LB_METHOD_%s" % lb_method.strip().upper()
    # is order necessary?
    api.GlobalLB.PoolV2.create(pools=[pool], lb_methods=[lb_method],
                               members=[[]], orders=[[]])
def remove_pool(api, pool):
    api.GlobalLB.PoolV2.delete_pool(pools=[pool])

def main():
    state_method_choices = ['state_disabled', 'state_enabled']
    lb_method_choices = ['return_to_dns', 'null', 'round_robin',
                         'ratio', 'topology', 'static_persist', 'global_availability',
                         'vs_capacity', 'least_conn', 'lowest_rtt', 'lowest_hops',
                         'packet_rate', 'cpu', 'hit_ratio', 'qos', 'bps',
                         'drop_packet', 'explicit_ip', 'connection_rate', 'vs_score']

    module = AnsibleModule(
        argument_spec = dict(
            server = dict(type='str', required=True),
            user = dict(type='str', required=True),
            password = dict(type='str', required=True, no_log=True),
            state = dict(type='str', required=True, choices=['present', 'absent', 'enabled', 'disabled']),
            pool = dict(type='str', required=True),
            partition = dict(type='str', default='Common'),
            virtual_server_server = dict(type='str', required=False),
            virtual_server_name = dict(type='str', required=False),
            lb_method = dict(type='str', choices=lb_method_choices, default='round_robin')
        ),
        supports_check_mode=True
    )

    if not bigsuds_found:
        module.fail_json(msg="the python bigsuds library is required")

    server = module.params['server']
    user = module.params['user']
    password = module.params['password']
    state = module.params['state']
    partition = module.params['partition']

    if partition not in module.params['pool']:
        pool = "/%s/%s" % (partition, module.params['pool'])
    else:
        pool = module.params['pool']

    pool_id = {'pool_name': pool, 'pool_type': 'GTM_QUERY_TYPE_A'}
    virtual_server_name = module.params['virtual_server_name']
    virtual_server_server = module.params['virtual_server_server']
    lb_method = module.params['lb_method']

    try:
        api = bigip_api(server, user, password)

        result = {'changed': False}  # default

        if state == 'enabled':
            if not pool_exists(api, pool_id):
                module.fail_json(msg="pool %s does not exist" % pool)
            if state != get_pool_state(api, pool_id):
                if not module.check_mode:
                    set_pool_state(api, pool_id, state)
                    result = {'changed': True}
                else:
                    result = {'changed': True}
        elif state == 'disabled':
            if not pool_exists(api, pool_id):
                module.fail_json(msg="pool %s does not exist" % pool)
            if state != get_pool_state(api, pool_id):
                if not module.check_mode:
                    set_pool_state(api, pool_id, state)
                    result = {'changed': True}
                else:
                    result = {'changed': True}
    except Exception, e:
        module.fail_json(msg="received exception: %s" % e)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
