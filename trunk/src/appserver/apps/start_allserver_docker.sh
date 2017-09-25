#!/bin/bash

cd user_srv_d/
exec nohup sh start.sh & $*

cd ../msg_srv_d/
exec nohup sh start.sh & $*

cd ../file_srv_d/
exec nohup sh start.sh & $*

cd ../terminal_srv_d/
exec nohup sh start.sh & $*

