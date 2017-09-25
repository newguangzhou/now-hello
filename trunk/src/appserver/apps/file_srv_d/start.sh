#!/bin/bash

source ../../pyenv/bin/activate

if [ ! -d /data/logs/file_srv_d ]; then
	mkdir -p /data/logs/file_srv_d
fi
exec python ./main.py --log_file_prefix=/data/logs/file_srv_d/file_srv_d.log --logging=debug $*

