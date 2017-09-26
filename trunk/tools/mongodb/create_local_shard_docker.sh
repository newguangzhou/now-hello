#!/bin/bash

for port in 27018 27019 27020
do
	extra_opts=""
	if [ "${port}" = "27020" ]; then
		extra_opts="--other-repl-hosts 127.0.0.1:27018,127.0.0.1:27019"
	fi

	python ./create.py --ip 127.0.0.1 --no-bind --port ${port} --name mongo_shard1 ${extra_opts}
done

/bin/bash
