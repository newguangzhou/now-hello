#!/bin/bash

source ../../pyenv/bin/activate

if [ ! -d /data/logs/self_srv_d ]; then
	mkdir -p /data/logs/self_srv_d
fi
exec python ./main.py --log_file_prefix=/data/logs/self_srv_d/self_srv_d.log --logging=debug $*

