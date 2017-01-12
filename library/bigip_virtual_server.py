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
module: bigip_virtual_server
short_description: "Manages F5 BIG-IP LTM virtual servers"
description:
    - "Manages F5 BIG-IP LTM virtual servers"
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
            - Virtual server state
        required: true
        choices: ['present', 'absent','enabled','disabled']
    name:
        description:
            - Virtual server name
        required: True
'''

EXAMPLES = '''
  - name: Enable virtual server
    local_action: >
      bigip_virtual_server
      server=192.168.0.1
      user=admin
      password=mysecret
      name=myname
      state=enabled
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

def virtual_server_exists(api, name):
    # hack to determine if virtual server exists
    result = False
    try:
        api.LocalLB.VirtualServer.get_object_status([name])
        result = True
    except bigsuds.OperationFailed, e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result

def get_virtual_server_state(api, name):
    state = api.LocalLB.VirtualServer.get_enabled_state([name])
    state = state[0].split('STATE_')[1].lower()
    return state

def get_system_active_folder(api):
    folder = api.System.Session.get_active_folder()
    return folder

def set_virtual_server_state(api, name, state):
    state = "STATE_%s" % state.strip().upper()
    api.LocalLB.VirtualServer.set_enabled_state([name], [state])
    
def set_system_active_folder(api, folder):
    api.System.Session.set_active_folder(folder)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            server = dict(type='str', required=True),
            user = dict(type='str', required=True),
            password = dict(type='str', required=True, no_log=True),
            name = dict(type='str', required=True),
            state = dict(type='str', required=True, choices=['enabled', 'disabled'])
        ),
        supports_check_mode=True
    )

    if not bigsuds_found:
        module.fail_json(msg="the python bigsuds module is required")

    server = module.params['server']
    user = module.params['user']
    password = module.params['password']
    name = module.params['name']
    state = module.params['state']
    
    partition = name.split('/')[1]
    full_path_partition = '/{0}'.format(partition)

    result = {'changed': False}  # default

    try:
        api = bigip_api(server, user, password)
        
        current_folder = get_system_active_folder(api)
        if partition != current_folder:
            set_system_active_folder(api, full_path_partition)

        if state == 'enabled':
            if not virtual_server_exists(api, name):
                module.fail_json(msg="virtual server does not exist")
            if state != get_virtual_server_state(api, name):
                if not module.check_mode:
                    set_virtual_server_state(api, name, state)
                    result = {'changed': True}
                else:
                    result = {'changed': True}
        elif state == 'disabled':
            if not virtual_server_exists(api, name):
                module.fail_json(msg="virtual server does not exist")
            if state != get_virtual_server_state(api, name):
                if not module.check_mode:
                    set_virtual_server_state(api, name, state)
                    result = {'changed': True}
                else:
                    result = {'changed': True}

    except Exception, e:
        module.fail_json(msg="received exception: %s" % e)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
