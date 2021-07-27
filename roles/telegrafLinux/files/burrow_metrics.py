#!/bin/python
import urllib2
import json

# weather,location=us-midwest temperature=82 1465839830100400200
#   |    -------------------- --------------  |
#   |             |             |             |
#   |             |             |             |
# +-----------+--------+-+---------+-+---------+
# |measurement|,tag_set| |field_set| |timestamp|
# +-----------+--------+-+---------+-+---------+

url = "http://localhost:9000"
message = ""
lag = 0
partition_count = 0
average_lag = 0

def get_clusters():
  full_url = "{0}/v2/kafka".format(url)
  response = urllib2.urlopen(full_url)
  data = json.load(response)
  return data['clusters']
  #return "loadtest_A"

def get_consumers(url, cluster):
  full_url = "{0}/v2/kafka/{1}/consumer/".format(url, cluster)
  response = urllib2.urlopen(full_url)
  data = json.load(response)
  return data

def get_lag(url, cluster, consumer):
  full_url = "{0}/v2/kafka/{1}/consumer/{2}/lag".format(url, cluster, consumer)
  response = urllib2.urlopen(full_url)
  data = json.load(response)
  return data

clusters = get_clusters()
for cluster in clusters:
  data = get_consumers(url, cluster)
  consumers = data['consumers']

  for consumer in consumers:
    # TODO: Make this a template
    data = get_lag(url, cluster, consumer)
    message += 'kafka_consumers,cluster="{0}" consumer_group="{1}",status="{2}"\n'.format(cluster,consumer, data['status']['status'])
    partition_count = len(data['status']['partitions'])
    for partition in data['status']['partitions']:
      message += 'kafka_burrow,cluster="{0}" consumer_group="{1}",partition="{2}",end_lag="{3}",status="{4}"\n'.format(cluster,consumer, partition['partition'], partition['end']['lag'],partition['status'])
      lag += partition['end']['lag']
    if lag > 0:
      average_lag = lag / partition_count
  #message += "kafka,consumer_group={1}\n".format("loadtest_A",consumer)

print message
