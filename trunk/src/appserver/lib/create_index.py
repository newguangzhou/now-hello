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
from config import *

conf = loadJsonConfig("../configs/config.json")
default_meta = conf["mongodb"]

extra_args = {"w": 1, "j": True}

mongo_client = pymongo.MongoClient(default_meta["hosts"], default_meta["port"],
                                                         **extra_args)
mongo_client.get_database("admin").authenticate(
                default_meta["username"],
                default_meta["passwd"],
                mechanism="SCRAM-SHA-1")

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
