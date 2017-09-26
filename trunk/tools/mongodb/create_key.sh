#!/bin/bash

if [ -z "$1" ]; then
	echo "Please give a file name"
	exit 1
fi

pk_path=`which openssl`
if [ -z "$pk_path" ]; then
    echo "installing openssl "
    apt-get install -y openssl
fi

openssl rand -base64 741 > $1

chmod 600 $1

