#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, Michael Perzel
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
module: bigip_sys_connection
short_description: "Run commands on F5 devices via api"
description:
    - "Run commands on F5 devices via api"
version_added: "2.2"
author: 'Michael Perzel'
notes:
    - "F5 developed module 'f5-sdk' required"
    - "Best run as a local_action in your playbook"
    - "Requires administrative privileges for user"

requirements:
    - f5-sdk
options:
    server:
        description:
            - BIG-IP host
        required: true
        default: null
        choices: []
        aliases: []
    user:
        description:
            - BIG-IP username
        required: true
        default: null
        choices: []
        aliases: []
    password:
        description:
            - BIG-IP password
        required: true
        default: null
        choices: []
        aliases: []
    command:
        description:
            - Command to run
        required: true
        choices: []
        aliases: []
'''

EXAMPLES = '''
- name: Show connections to LTM virtual server
  local_action: >
      bigip_sys_connection
      server={{ f5_ltm_server }}
      user={{ f5_ltm_username }}
      password={{ f5_ltm_password }}
      command="tmsh show sys connection cs-server-addr {{ ip_address }}"
'''
try:
    from f5.bigip import ManagementRoot
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False

def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")
    argument_spec = f5_argument_spec()

    meta_args = dict(
        command=dict(type='str', required=True),
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    server = module.params['server']
    user = module.params['user']
    password = module.params['password']
    # server_port = module.params['server_port']
    # validate_certs = module.params['validate_certs']
    command = '-c "{0}"'.format(module.params['command'])
    
    result = {}
    result['changed'] = False
    
    try:
        mgmt = ManagementRoot(server, user, password)
        output = mgmt.tm.util.bash.exec_cmd('run', utilCmdArgs=command)
    
        if hasattr(output, 'commandResult'):
            result['msg'] = output.commandResult

        result['changed'] = True

    except Exception as e:
        module.fail_json(msg="received exception: {0}".format(e))

    module.exit_json(**result)


# include magic from lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()