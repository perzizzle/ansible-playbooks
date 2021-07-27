#!/bin/python

import subprocess
import os

os.environ['LD_LIBRARY_PATH']='/data01/app/oracle/product/19.0.0/db_1/lib:/acfsvol1/ogg/current'

def run_command(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    try:
        outs, errs = proc.communicate()
        lines = outs.splitlines()
        errors = errs.splitlines()

        if proc.returncode != 0 and len(errors) > 0:
            print("Return code: {0}".format(proc.returncode))
            print(errors)

        return lines

    except Exception as e:
        print("ERROR: {0}".format(e))
        proc.kill()

def convert_to_seconds(time):
  h, m, s = time.split(':')
  return int(h) * 3600 + int(m) * 60 + int(s)

command = 'echo "info all" | /acfsvol1/ogg/current/ggsci | egrep "EXTRACT|REPLICAT"'
process_check = 'ps -ef | grep -v grep | grep /acfsvol1/ogg/current/ggsci'
lines = run_command(process_check)
if len(lines) > 0:
  exit()

lines = run_command(command)

for line in lines:
    stream = line.split()
    print ('ogg_lag,name={2},type={0} status="{1}",lag_time_seconds={3},stopped_time={4}').format(stream[0],stream[1],stream[2],convert_to_seconds(stream[3]),convert_to_seconds(stream[4]))