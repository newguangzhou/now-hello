#!/bin/bash

if [ -z "$1" ]; then
	echo "Please give username"
	exit 1
fi

if [ -z "$2" ]; then
	echo "Please give passwd"
	exit 1
fi

username=$1
passwd=$2

shift 2

eval_str="db.getMongo().getDB('admin').createUser({user:'${username}', pwd:'${passwd}', roles:[{role:'readWriteAnyDatabase', db:'admin'}, {role:'userAdminAnyDatabase', db:'admin'}, {role:'clusterAdmin', db:'admin'}, {role:'dbAdminAnyDatabase', db:'admin'}]})"

mongo 127.0.0.1:27020 $* --eval "$eval_str"


