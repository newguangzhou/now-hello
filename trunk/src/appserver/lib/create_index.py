# -*- coding: utf-8 -*-

import sys
import pymongo
sys.path.append("../")
from global_mongo_defines import *
from new_device_mongo_defines import *
from op_log_mongo_defines import *
from pet_mongo_defines import *
from user_mongo_defines import *
from auth_mongo_defines import *

class MongoMeta:
    def __init__(self, *args, **kwargs):
        self.host = "172.19.101.61"
        self.port = 27017
        self.username = None
        self.passwd = None
        self.repl_set_name = None
        self.max_thread_count = 3

        if kwargs.has_key("hosts"):
            self.host = kwargs["hosts"]
        if kwargs.has_key("port"):
            self.port = kwargs["port"]

        if kwargs.has_key("username"):
            self.username = kwargs["username"]

        if kwargs.has_key("passwd"):
            self.passwd = kwargs["passwd"]

        if kwargs.has_key("repl_set_name"):
            self.repl_set_name = kwargs["repl_set_name"]

        if kwargs.has_key("max_thread_count"):
            self.max_thread_count = kwargs["max_thread_count"]

hosts = "172.17.0.2:27018,172.17.0.2:27019,172.17.0.2:27020"
hosts = "127.0.0.1:27018,127.0.0.1:27019,127.0.0.1:27020"
default_meta = MongoMeta(hosts=hosts,
                                      port=27020,
                                      username="root",
                                      passwd="mgdb8w34asdadat51!((",
                                      repl_set_name="mongo_shard1")

extra_args = {"w": 1, "j": True}

mongo_client = pymongo.MongoClient(default_meta.host, replicaset=default_meta.repl_set_name,
                                                         **extra_args)
mongo_client.get_database("admin").authenticate(
                default_meta.username,
                default_meta.passwd,
                mechanism='SCRAM-SHA-1')

def create_auth_indexes():
    tb = mongo_client[AUTH_DATABASE][AUTH_STATUS_TB]
    tb.create_indexes(AUTH_STATUS_TB_INDEXES)
    tb = mongo_client[AUTH_DATABASE][AUTH_INFOS_TB]
    tb.create_indexes(AUTH_INFOS_TB_INDEXES)

def create_user_indexes():
    tb = mongo_client[USER_DATABASE][USER_LOGIN_STATUS_TB]
    tb.create_indexes(USER_LOGIN_STATUS_TB_INDEXES)
    tb = mongo_client[USER_DATABASE][USER_INFOS_TB]
    tb.create_indexes(USER_INFOS_TB_INDEXES)

def create_pet_indexes():
    tb = mongo_client[PET_DATABASE][PET_INFOS_TB]
    tb.create_indexes(PET_INFOS_TB_INDEXES)
    tb = mongo_client[PET_DATABASE][PET_LOCATION_INFOS_TB]
    tb.create_indexes(PET_LOCATION_INFOS_TB_INDEXES)
    tb = mongo_client[PET_DATABASE][PET_SPORT_INFOS_TB]
    tb.create_indexes(PET_SPORT_INFOS_TB_INDEXES)
    tb = mongo_client[PET_DATABASE][PET_SLEEP_INFOS_TB]
    tb.create_indexes(PET_SLEEP_INFOS_TB_INDEXES)

def create_device_indexes():
    tb = mongo_client[DEVICE_DATABASE][DEVICE_INFOS_TB]
    tb.create_indexes(DEVICE_INFOS_TB_INDEXES)
    tb = mongo_client[DEVICE_DATABASE][DEVICE_WIFI_INFOS_TB]
    tb.create_indexes(DEVICE_WIFI_INFOS_TB_INDEXES)
    tb = mongo_client[DEVICE_DATABASE][DEVICE_SPORT_INFOS_TB]
    tb.create_indexes(DEVICE_SPORT_INFOS_TB_INDEXES)
    tb = mongo_client[DEVICE_DATABASE][DEVICE_SLEEP_INFOS_TB]
    tb.create_indexes(DEVICE_SLEEP_INFOS_TB_INDEXES)

def create_op_log_indexes():
    tb = mongo_client[OP_LOG_DATABASE][OP_LOG_INFOS_TB]
    tb.create_indexes(OP_LOG_INFOS_TB_INDEXES)

def create_global_indexes():
    tb = mongo_client[GLOBAL_DATABASE][SYS_CONFIG_TB]
    tb.create_indexes(SYS_CONFIG_TB_INDEXES)
    tb = mongo_client[GLOBAL_DATABASE][GID_ALLOC_STATUS_TB]
    tb.create_indexes(GID_ALLOC_STATUS_TB_INDEXES)

create_device_indexes()
create_global_indexes()
create_op_log_indexes()
create_pet_indexes()
create_auth_indexes()
create_user_indexes()