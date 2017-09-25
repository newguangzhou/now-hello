#!/bin/bash

source ../../pyenv/bin/activate

if [ ! -d /data/logs/msg_srv_d ]; then
	mkdir -p /data/logs/msg_srv_d
fi

exec python ./main.py --log_file_prefix=/data/logs/msg_srv_d/msg_srv_d.log --logging=debug $*

