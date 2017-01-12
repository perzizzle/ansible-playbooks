#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: oracle_query
short_description: This module allows you to run ad-hoc oracle queries
description:
    - Run ad-hoc oracle queries
version_added: "1.0"
options:
    host:
        description:
            - The Oracle database node
        required: false
        default: localhost
    user:
        description:
            - The Oracle user name
        required: true
    password:
        description:
            - The Oracle user password
        required: true
    port:
        description:
            - The TNS port to connect to
        required: false
        default: 1521
    name:
        description:
            - The SID or service name
        required: true
    connection:
        description:
            - Specify to connect with SID or service name
        required: true
    query:
        description:
            - ad-hoc oracle query to run or path to file of queries
        required: true
    input:
        description:
            - Is the input an ad-hoc query or a file of queries
        options:
            - ad-hoc
            - file
        default: ad-hoc
notes:
    - Requires the installation of cx_Oracle
requirements: [ "cx_Oracle" ]
'''

EXAMPLES = '''
# Run query on server oracleserver.com using a service name of orcl authenticating as mperzel with password password123
- oracle_query host=oracleserver.com user=mperzel password=password123 connection=service_name name=orcl query='select table_name from all_tables'
'''

import ConfigParser
import os
import warnings
import cx_Oracle
import string
import sys
import getopt

def main():

    mess = ''
    module = AnsibleModule(
            argument_spec = dict(
            host=dict(default="localhost"),
            user=dict(required=True),
            password=dict(required=True),
            port=dict(default=1521),
            name=dict(required=True),
            connection=dict(default='service_name', choices=['sid','service_name']),
            query=dict(required=True),
            input=dict(default='ad-hoc', choices=['ad-hoc','file']),
        )
    )

    host = module.params["host"]
    user = module.params["user"]
    password = module.params["password"]
    port = module.params["port"]
    name = module.params["name"]
    query = module.params["query"]
    connection = module.params["connection"]
    input = module.params["input"]

    if len(query) == 0:
        mess = 'Query must be provided, cannot be 0 characters long'
        module.fail_json(msg=mess, changed=False)

    if connection == 'sid':
        dsn = cx_Oracle.makedsn (host, port, name)
    elif connection == 'service_name':
        dsn = cx_Oracle.makedsn (host, port, service_name = name)

    try:
        # Connect to Oracle...
        con = cx_Oracle.connect (user, password, dsn)

        # Initialize output variable
        output = {}



    except cx_Oracle.DatabaseError as e:
        error, = e.args
        mess = error.message
        module.fail_json(msg=mess, changed=False)
        raise

    # determine type of query and make upper case for comparison
    type = query.split(' ', 1)[0].upper()

    cur = con.cursor()
    if input == 'ad-hoc':
        try:
            # Remove semi-colon if there is one in the query
            query = query.translate(None,';')
            cur.execute(query)
            if type == 'SELECT':
                for count, row in enumerate(cur):
                    output[count] = row
            elif type == 'UPDATE':
                con.commit()
                output['count'] = cur.rowcount
            else:
                mess = "Query type of {0} not support".format(type)
                module.fail_json(msg=mess, changed=False)
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            mess = query + "->" + error.message
            module.fail_json(msg=mess, changed=False)
            raise
    elif input == 'file':
        sqlQuery = ''
        output = ''
        #Open file and start running queries
        with open(query, 'r') as inp:
            lineNo = 0
            for line in inp:
                lineNo = lineNo + 1
                line = line.strip()
                line = line.lstrip()
                # Skip any blank lines or SQL remark characters
                if line == '\n' or line.find('--',0,2) != -1 or line.find('REM',0,3) != -1:
                    sqlQuery = ''
                else:
                    #If line ends in semicolon but isn't a comment try to run query
                    sqlQuery = line
                    sqlQuery = sqlQuery.strip()
                    sqlQuery = sqlQuery.strip(';')
                    sqlQuery = sqlQuery.strip('/')
                    sqlQuery = sqlQuery.strip('\n')

                    try:
                        cur.execute(sqlQuery)
                    except cx_Oracle.DatabaseError as e:
                        error, = e.args
                        mess = "Line: "+str(lineNo)+": "+sqlQuery + "->" + error.message
                        module.fail_json(msg=mess, changed=False)
                        raise

                    output = output + str(lineNo) + ": Command Processed"

                # Clear out sqlQuery for next loop
                sqlQuery = ''

    try:
        if input == 'file':
            inp.close()
        cur.close()
        con.close()
    except cx_Oracle.DatabaseError:
        pass

#    module.exit_json(msg=mess, changed=True)
    module.exit_json(msg=output, changed=True)

from ansible.module_utils.basic import *
main()