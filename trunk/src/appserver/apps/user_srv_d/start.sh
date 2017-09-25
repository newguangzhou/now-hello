#!/bin/bash

source ../../pyenv/bin/activate

if [ ! -d /data/logs/user_srv_d ]; then
	mkdir -p /data/logs/user_srv_d
fi
exec python ./main.py --log_file_prefix=/data/logs/user_srv_d/user_srv_d.log --logging=debug $*

