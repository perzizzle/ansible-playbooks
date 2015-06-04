#!/usr/bin/python
# -*- coding: utf-8 -*-
# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: unzip
version_added: "1.8"
short_description: Unzips files on windows machines
description:
     - Unzips files on windows machines
options:
  destination:
    description:
      - Destination for unzipped files
    required: true
    default: null
    aliases: []
    source:
    description:
      - Source of zip file
    required: true
    default: null
    aliases: []
    include:
    description:
      - Include this file when unzipped
    required: false
    exclude:
    description:
      - Exclude this file when unzipped
    required: false
    creates:
    description:
      - Only unzip if this file does not already exist
    required: false 
author: Michael Perzel / Justin Rocco
'''

EXAMPLES = '''
# This unzips a file
$ ansible -i hosts -m unzip -a "source=file.zip destination=c:\" all


# Playbook example
---
- name: Unzip file
  hosts: all
  gather_facts: false
  tasks:
    - name: Unzip file
      unzip: source=C:\File.zip destination=C:\

'''