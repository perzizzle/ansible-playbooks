#!/bin/bash
QM_01=$(netstat -an | grep 10101 | wc -l)
QM_02=$(netstat -an | grep 10102 | wc -l)
echo "mq_connections,port=10101,queue_manager=SS_QM_01 connections=$QM_01"
echo "mq_connections,port=10102,queue_manager=SS_QM_02 connections=$QM_02"