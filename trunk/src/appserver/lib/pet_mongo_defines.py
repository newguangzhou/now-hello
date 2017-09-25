# -*- coding: utf-8 -*-

import copy
import datetime

import pymongo
from pymongo.operations import IndexModel

from lib import utils

PET_DATABASE = "xmq_pet"
"""
宠物基本信息表
"""
PET_INFOS_TB = "pet_infos"
PET_INFOS_TB_INDEXES = [
    IndexModel("pet_id", unique=True),
    IndexModel("device_imei", unique=True),
    IndexModel("uid"),
]
_PET_INFOS_TB_ROW_DEFINE = {
    "pet_id": (None, int),  # 宠物全局唯一ID
    "uid": (None, int),
    "nick": (u"", unicode),
    "logo_url": (u"", unicode),
    "logo_small_url": (u"", unicode),
    "birthday": (datetime.datetime(1970, 1, 1), datetime.datetime),
    "device_type": None,  # 设备类型
    "sex": (0, int),
    "weight": (0, float),
    "pet_type_id": (None, int),
    "description": (u"", unicode),
    "register_date": (None, datetime.datetime),
    "mod_date": (None, datetime.datetime),
    "device_imei": (None, unicode),
    "target_step": (0, int),
    "target_energy": (0, float),
    "recommend_energy": (0, float),
    "pet_status": (0, int),
    "pet_no_search_status": (0, int),#只记录遛狗和在家两种状态  方便前台关闭gps后返回之前的状态
    "pet_is_in_home": (1,int), # 1 在家  0 不在家
    "home_wifi": (None, dict),
    "home_location": (None,dict),
    "common_wifi": ([], list),
    "has_reboot":(0,int),
    "device_status":(1,int), #设备状态  0表示离线，1表示在线
    "device_os_int": (23, int),  # android 设备os  int 值
    "mobile_num": None,  # 手机号码
    "agree_policy":(0,int), #0是不同意，1是同意
}

"""
狗睡眠信息
"""
PET_SLEEP_INFOS_TB = "pet_sleep_info"
PET_SLEEP_INFOS_TB_INDEXES = [IndexModel("pet_id"), IndexModel("begin_time")]
PET_SLEEP_TB_ROW_DEFINE = {
    "pet_id": (None, int),
    "device_imei": (u"", unicode),
    "begin_time": (None, datetime.datetime),
    "total_secs": (0, int),
    "quality": (0, int),
    #"location"
}
"""
狗运动信息
"""
PET_SPORT_INFOS_TB = "pet_sport_info"
PET_SPORT_INFOS_TB_INDEXES = [IndexModel(
    [("pet_id", pymongo.DESCENDING), ("diary", pymongo.ASCENDING)])]
PET_SPORT_TB_ROW_DEFINE = {
    "pet_id": (None, int),
    "device_imei": (u"", unicode),
    "diary": (None, datetime.datetime),
    "step_count": (0, int),
    "distance": (0, int),
    "target_energy": (0,float),
    "calorie": (0, int),
    #"location"
}
"""
狗位置信息
"""
PET_LOCATION_INFOS_TB = "pet_location_info"
PET_LOCATION_INFOS_TB_INDEXES = [IndexModel("pet_id"),
                                 IndexModel("device_imei")]
PET_LOCATION_TB_ROW_DEFINE = {
    "pet_id": (None, int),
    "device_imei": (u"", unicode),
    "locator_time": (None, datetime.datetime),
    "server_recv_time":(None,int),
    "lnglat": ([], list),
    "lnglat2": ([], list),
    "lnglat3": ([], list),
    "radius": (0, int),
    "radius2": (0, int),
    "radius3": (0, int),
    "locator_status":(5,int),
    #"location"
}


def new_pet_sleep_row():
    tmp = utils.new_mongo_row(PET_SLEEP_TB_ROW_DEFINE)
    return tmp


def new_pet_sport_row():
    tmp = utils.new_mongo_row(PET_SPORT_TB_ROW_DEFINE)
    return tmp


def new_pet_location_row():
    tmp = utils.new_mongo_row(PET_LOCATION_TB_ROW_DEFINE)
    return tmp

def new_pet_wifi_row():
    tmp = utils.new_mongo_row(PET_WIFI_TB_ROW_DEFINE)
    return tmp


def new_pet_infos_row():
    tmp = utils.new_mongo_row(_PET_INFOS_TB_ROW_DEFINE)
    cur = datetime.datetime.today()
    tmp["register_date"] = cur
    tmp["mod_date"] = cur
    return tmp


def validate_pet_infos_row(row):
    return utils.validate_mongo_row(row, _PET_INFOS_TB_ROW_DEFINE)


def validate_pet_infos_cols(**cols):
    return utils.validate_mongo_row_cols(_PET_INFOS_TB_ROW_DEFINE, **cols)


def has_pet_infos_col(colname):
    return utils.has_mongo_row_col(_PET_INFOS_TB_ROW_DEFINE, colname)