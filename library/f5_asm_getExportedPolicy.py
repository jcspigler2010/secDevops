#!/usr/bin/python
# -*- coding: utf-8 -*-
#

DOCUMENTATION = '''
'''

EXAMPLES = '''
'''

import socket


try:
    import json
    import requests
except ImportError:
    requests_found = False
else:
    requests_found = True


class BigIpCommon(object):
    def __init__(self, module):
        self._username = module.params.get('user')
        self._password = module.params.get('password')
        self._serviceName = module.params.get('serviceName')
        self._hostname = module.params.get('server')
        self._validate_certs = module.params.get('validate_certs')


class BigIpRest(BigIpCommon):
    def __init__(self, module):
        super(BigIpRest, self).__init__(module)

        self._uri = 'https://%s/mgmt/tm/asm/file-transfer/downloads/%s.xml' % (self._hostname,self._serviceName)

        self._headers = {
            'Content-Type': 'application/json'
        }

        self._payload = {}


    def run(self):
        policyId = ""

        resp = requests.get(self._uri,
                            auth=(self._username, self._password),
                            verify=self._validate_certs)



        if resp.status_code == 200:
	        f = open( self._serviceName + ".xml","w")
        	f.write(resp.text)
        	f.close()

        else:
            res = resp.json()
            raise Exception(res['message'])
        return policyId


def main():
    changed = False


    module = AnsibleModule(
       argument_spec=dict(
            server=dict(required=True),
            partition=dict(default='Common'),
            name=dict(default=''),
            user=dict(required=True, aliases=['username']),
            password=dict(required=True),
	    serviceName=dict(required=True),
            validate_certs=dict(default='no', type='bool')
        )
    )


    obj = BigIpRest(module)

    if obj.run():
    	changed = True

    module.exit_json(changed=changed)


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
