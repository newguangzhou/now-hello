#!/bin/bash

for port in 27018 27019 27020
do
	extra_opts=""
	if [ "${port}" = "27020" ]; then
		extra_opts="--other-repl-hosts 192.168.111.169:27018,192.168.111.169:27019"
	fi

	python ./create.py --ip 192.168.111.169 --no-bind --port ${port} --name mongo_shard1 ${extra_opts}
done
