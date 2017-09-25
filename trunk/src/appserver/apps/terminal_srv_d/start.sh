#!/bin/bash

source ../../pyenv/bin/activate

if [ ! -d /data/logs/terminal_srv_d ]; then
	mkdir -p /data/logs/terminal_srv_d
fi
exec python ./main.py --log_file_prefix=/data/logs/terminal_srv_d/terminal_srv_d.log $*

