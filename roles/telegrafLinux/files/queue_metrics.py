#!/bin/python

import subprocess
import re

queue_mgrs = ["SS_QM_01", "SS_QM_02"]
queue_prefixes = ["SS", "RXH"]
execute = True


def run_command(cmd):

    if not execute:
        return()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    try:
        outs,errs = proc.communicate()
        errors = errs.splitlines()

        if proc.returncode != 0 and len(errors) > 0:
            print("Return code: {0}".format(proc.returncode))
            print(errors)

        return outs

    except Exception as e:
        print("ERROR: {0}".format(e))
        proc.kill()

def get_queue_depth(queue_mgr, queue_search_string):
    command = "echo 'display qstatus ({0}*) curdepth, msgage, lputtime, monq' | sudo -u mqm /app/mqm/bin/runmqsc {1}".format(queue_search_string, queue_mgr)
    process_check = 'ps -ef | grep -v grep | grep /app/mqm/bin/runmqsc | grep -v qstatus'
    lines = run_command(process_check)
    if len(lines) > 0:
        exit()
    
    mq_resp = run_command(command)
    lines = mq_resp.split("AMQ")
    # run_command method executes command to retrieve all queue metrics we want,
    # then it splits it into chunks that will look like this:
    # 8450: Display queue status details.
    # QUEUE(RXH.ENT.AGGREGATED)               TYPE(QUEUE)
    # CURDEPTH(0)                             LPUTTIME( )
    # MONQ(OFF)                               MSGAGE( )

    metrics = {}

    for line in lines:
        if re.search(r'.*QUEUE\((.*)\).*\(.*\).*', line, re.M):
            # if we find 'QUEUE(*)', we can proceed with parsing out relevant values
            name = re.search(r'.*QUEUE\((.*)\).*\(.*\).*', line, re.M).group(1)
            depth = re.search(r'.*CURDEPTH\((.*)\).*\(.*\).*', line, re.M).group(1)
            lputtime = re.search(r'.*LPUTTIME\((.*)\).*', line, re.M).group(1)
            monq = re.search(r'.*MONQ\((.*)\).*\(.*\).*', line, re.M).group(1)
            msgage = re.search(r'.*MSGAGE\((.*)\).*', line, re.M).group(1)

            # need to be able to differentiate between an expected null value and a null value because monitoring
            # is turned off. if monq = OFF, we will not get  values for msgage or lputtime
            if monq == "OFF":
                lputtime = "-2"
                msgage = "-2"
            else:
                if lputtime.isspace() or not lputtime:
                    lputtime = "-1"
                if msgage.isspace() or not msgage:
                    msgage = "-1"
            metrics[name] = [depth, lputtime, monq, msgage]

    return metrics


queue_metrics = {}

for queue_mgr in queue_mgrs: 

    for queue_prefix in queue_prefixes:
        queue_metrics = get_queue_depth(queue_mgr, queue_prefix)
        
        for key,values in queue_metrics.items():
           print ('mq_queue,queue_mgr={0},queues={1} depth={2}').format(queue_mgr, key, int(values[0]))
           print ('mq_queue,queue_mgr={0},queues={1} lputtime="{2}"').format(queue_mgr, key, values[1])
           print ('mq_queue,queue_mgr={0},queues={1} monq="{2}"').format(queue_mgr, key, values[2])
           print ('mq_queue,queue_mgr={0},queues={1} msgage={2}').format(queue_mgr, key, int(values[3]))