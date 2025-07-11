#!/bin/bash

DATA_DIR="/opt/hadoop/data/dataNode"

mkdir -p "$DATA_DIR"
chown -R hadoop:hadoop "$DATA_DIR"
chmod -R 755 "$DATA_DIR"

hdfs datanode
