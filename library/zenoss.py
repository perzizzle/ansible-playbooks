#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Liberally borrowed from https://github.com/iamseth/python-zenoss
# 2016, Michael Perzel

DOCUMENTATION = '''
---
module: zenoss
short_description: "Modify zenoss via api"
description:
    - "Modify zenoss via api"
version_added: "1.9"
author: 'Michael Perzel'
requirements:
    - requests
    - json
options:
    server:
        description:
            - zenoss host
        required: true
        default: null
        choices: []
        aliases: []
    username:
        description:
            - zenoss username
        required: true
        default: null
        choices: []
        aliases: []
    password:
        description:
            - zenoss user password
        required: true
        default: null
        choices: []
        aliases: []
    method:
        description:
            - zenoss method to evoke
        required: true
        default: null
        choices: ['get_devices', 'set_production_state']
        aliases: []
    device_name:
        description:
            - zenoss device_name
        required: true
        default: null
        choices: []
        aliases: []
    state:
        description:
            - maintenance mode state
        required: false
        default: null
        choices: []
        aliases: []

'''

EXAMPLES = '''
  - name: Set maintenance mode on device
    zenoss
      server=https://zenoss.surescripts.internal
      username=admin
      password=mysecret
      method=set_production_state
      path='Server/SSH/Linux/asrv/devices/mll-asrv01a.surescripts-lt.ext'
      state=300
'''
'''Python module to work with the Zenoss JSON API
Liberally borrowed from https://github.com/iamseth/python-zenoss
'''
import re
import json
import requests

requests.packages.urllib3.disable_warnings()

ROUTERS = {'MessagingRouter': 'messaging',
           'EventsRouter': 'evconsole',
           'ProcessRouter': 'process',
           'ServiceRouter': 'service',
           'DeviceRouter': 'device',
           'NetworkRouter': 'network',
           'TemplateRouter': 'template',
           'DetailNavRouter': 'detailnav',
           'ReportRouter': 'report',
           'MibRouter': 'mib',
           'ZenPackRouter': 'zenpack'}


class ZenossException(Exception):
    '''Custom exception for Zenoss
    '''
    pass


class Zenoss(object):
    '''A class that represents a connection to a Zenoss server
    '''
    def __init__(self, host, username, password, ssl_verify=True):
        self.__host = host
        self.__session = requests.Session()
        self.__session.auth = (username, password)
        self.__session.verify = ssl_verify
        self.__req_count = 0

    def __router_request(self, router, method, data=None):
        '''Internal method to make calls to the Zenoss request router
        '''
        if router not in ROUTERS:
            raise Exception('Router "' + router + '" not available.')

        req_data = json.dumps([dict(
            action=router,
            method=method,
            data=data,
            type='rpc',
            tid=self.__req_count)])

        uri = '%s/zport/dmd/%s_router' % (self.__host, ROUTERS[router])
        headers = {'Content-type': 'application/json; charset=utf-8'}
        response = self.__session.post(uri, data=req_data, headers=headers)
        self.__req_count += 1

        # The API returns a 200 response code even whe auth is bad.
        # With bad auth, the login page is displayed. Here I search for
        # an element on the login form to determine if auth failed.

        if re.search('name="__ac_name"', response.content.decode("utf-8")):
            raise ZenossException('Request failed. Bad username/password.')

        return json.loads(response.content.decode("utf-8"))['result']

    def get_devices(self, device_class='/zport/dmd/Devices', limit=None, **kwargs):
        '''Get a list of all devices.

        '''
        return self.__router_request('DeviceRouter', 'getDevices',
                                     data=[{'uid': device_class, 'params': kwargs, 'limit': limit}])

    def get_components(self, device_name, **kwargs):
        '''Get components for a device given the name
        '''
        uid = self.device_uid(device_name)
        return self.get_components_by_uid(uid=uid, **kwargs)

    def get_components_by_uid(self, uid=None, meta_type=None, keys=None,
                              start=0, limit=50, page=0,
                              sort='name', dir='ASC', name=None):
        '''Get components for a device given the uid
        '''
        data = dict(uid=uid, meta_type=meta_type, keys=keys, start=start,
                    limit=limit, page=page, sort=sort, dir=dir, name=name)
        return self.__router_request('DeviceRouter', 'getComponents', [data])

    def set_components_monitored(self, component, monitor):
        '''Set monitor state for component
        '''
        # hash is set on the device not the component???
        data = dict(uids=[component['uid']], monitor=monitor, hashcheck=1)
        return self.__router_request('DeviceRouter', 'setComponentsMonitored', [data])

    def find_device(self, device_name):
        '''Find a device by name.

        '''
        all_devices = self.get_devices()

        try:
            device = [d for d in all_devices['devices'] if d['name'] == device_name][0]
            # We need to save the has for later operations
            device['hash'] = all_devices['hash']
            return device
        except IndexError:
            raise Exception('Cannot locate device %s' % device_name)

    def device_uid(self, device):
        '''Helper method to retrieve the device UID for a given device name
        '''
        return self.find_device(device)['uid']

    def add_device(self, device_name, device_class, collector='localhost'):
        '''Add a device.

        '''
        data = dict(deviceName=device_name, deviceClass=device_class, model=True, collector=collector)
        return self.__router_request('DeviceRouter', 'addDevice', [data])

    def remove_device(self, device_name):
        '''Remove a device.

        '''
        device = self.find_device(device_name)
        data = dict(uids=[device['uid']], hashcheck=device['hash'], action='delete')
        return self.__router_request('DeviceRouter', 'removeDevices', [data])

    def set_prod_state(self, device_name, prod_state):
        '''Set the production state of a device.

        '''
        device = self.find_device(device_name)
        data = dict(uids=[device['uid']], prodState=prod_state, hashcheck=device['hash'])
        return self.__router_request('DeviceRouter', 'setProductionState', [data])

    def set_maintenance(self, device_name):
        '''Helper method to set prodState for device so that it does not alert.

        '''
        return self.set_prod_state(device_name, 300)

    def set_production(self, device_name):
        '''Helper method to set prodState for device so that it is back in production and alerting.

        '''
        return self.set_prod_state(device_name, 1000)

def main():
    module = AnsibleModule(
            argument_spec = dict(
                    server = dict(type='str', required=True),
                    username = dict(type='str', required=True),
                    password = dict(type='str', required=True, no_log=True),
                    method = dict(type='str', required=True),
                    device_name = dict(type='str', required=True),
                    component_name=dict(type='str', required=False),
                    state = dict(type='int', required=False),
                    monitor=dict(type='bool', required=False),
            ),
            supports_check_mode=False
    )

    server = module.params['server']
    username = module.params['username']
    password = module.params['password']
    method = module.params['method']
    device_name = module.params['device_name']
    component_name = module.params['component_name']
    state = module.params['state']
    monitor = module.params['monitor']

    hashcheck = 1
    result = {'changed': False}  # default

    # initiate zenoss connection
    z = Zenoss(server, username, password, False)

    if method == 'get_devices':
        devices = z.get_devices(name=device_name)
        result['devices'] = devices['devices']
    elif method == 'get_production_state':
        devices = z.get_devices(name=device_name)
        state = devices['devices'][0]['productionState']
        result['production_state'] = state
        result['msg'] = "Device is in production state {0}".format(state)
    elif method == 'set_production_state':
        if state is None:
            module.fail_json(msg="State parameter is required")
        devices = z.get_devices(name=device_name)
        current_state = devices['devices'][0]['productionState']
        count = devices['totalCount']
        if count != 1:
            module.fail_json(msg="More than 1 device impacted, total devices impacted {0}".format(count))
        if current_state == state:
            result['msg'] = "Device already in production state {0}".format(state)
        else:
            z.set_prod_state(device_name, state)
            result['msg'] = "Device set to production state {0}".format(state)
            result['changed'] = True
    elif method == 'get_component':
        if component_name is None:
            module.fail_json(msg="Component name parameter is required")
        component = {}
        components = z.get_components(device_name=device_name)
        for temp_component in components['data']:
            if temp_component['name'] == component_name:
                component = temp_component
        if component:
            result['component'] = component
            result['changed'] = True
        else:
            module.fail_json(msg="Component is not in provided device")
    elif method == 'set_component_monitor':
        if component_name is None or monitor is None:
            module.fail_json(msg="Component name and monitor parameters are required")
        component = {}
        # could check to make sure the device exists first?
        components = z.get_components(device_name=device_name)
        for temp_component in components['data']:
            if temp_component['name'] == component_name:
                component = temp_component
                break
        if component:
            if component['monitored'] != monitor:
                response = z.set_components_monitored(component=component, monitor=monitor)
                result['msg'] = response['msg']
                result['changed'] = True
        else:
            module.fail_json(msg="Component: {0} is not in provided device: {1}".format(component_name, device_name))
    else:
        module.fail_json(msg="Unknown method: {0}".format(method))
    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
