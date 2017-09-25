# -*- coding: utf-8 -*-

import copy
import datetime

import pymongo
from pymongo.operations import IndexModel
import datetime
from lib import utils

DEVICE_DATABASE = "xmq_device2"
"""
设备信息
"""
DEVICE_INFOS_TB = "device_info"
DEVICE_INFOS_TB_INDEXES = [IndexModel("imei", uniq=True),]
DEVICE_TB_ROW_DEFINE = {
    "imei": (u"", unicode),
    "sleep_data": ([], list),
    "heart_rate_data": ([], list),
    "log_items": ([], list),
    "iccid": (u"", unicode),
    "hardware_version": (u"", unicode),
    "software_version": (u"", unicode),
    "electric_quantity": (-1, int),
    "j01_repoter_date": (None, datetime.datetime),
    "sim_deadline": (None, datetime.datetime),
    "location_data": ([], list),
    "light_status": (0, int),
    "device_name": (u"", unicode),  #设备名称
    "status": (0, int),  #报警状态
    "battery_status":(0,int), #电量状态 0 正常，1，低电量  2，超低电量
    "server_recv_time": (None, int),
    #"location"
}
"""
设备睡眠信息
"""
DEVICE_SLEEP_INFOS_TB = "device_sleep_info"
DEVICE_SLEEP_INFOS_TB_INDEXES = [IndexModel("imei"), IndexModel("begin_time")]
DEVICE_SLEEP_TB_ROW_DEFINE = {
    "imei": (u"", unicode),
    "begin_time": (None, datetime.datetime),
    "total_secs": (0, int),
    "quality": (0, int),
    #"location"
}
"""
设备运动信息
"""
DEVICE_SPORT_INFOS_TB = "device_sport_info"
DEVICE_SPORT_INFOS_TB_INDEXES = [IndexModel(
    [("imei", pymongo.DESCENDING), ("diary", pymongo.ASCENDING)])]
DEVICE_SPORT_TB_ROW_DEFINE = {
    "imei": (u"", unicode),
    "diary": (None, datetime.datetime),
    "step_count": (0, int),
    "distance": (0, int),
    "calorie": (0, int),
    #"location"
}
"""
设备wifi上报信息
"""
DEVICE_WIFI_INFOS_TB = "device_wifi_info"
DEVICE_WIFI_INFOS_TB_INDEXES = [IndexModel(
    [("imei", pymongo.DESCENDING), ("create_date", pymongo.ASCENDING)])]
DEVICE_WIFI_TB_ROW_DEFINE = {
    "imei": (u"", unicode),
    "create_date": (None, datetime.datetime),
    "wifi_info": (u"", unicode),
    #"location"
}


def new_device_row():
    tmp = utils.new_mongo_row(DEVICE_TB_ROW_DEFINE)
    return tmp


def new_device_sleep_row():
    tmp = utils.new_mongo_row(DEVICE_SLEEP_TB_ROW_DEFINE)
    return tmp


def new_device_sport_row():
    tmp = utils.new_mongo_row(DEVICE_SPORT_TB_ROW_DEFINE)

    return tmp


def new_device_wifi_row():
    tmp = utils.new_mongo_row(DEVICE_WIFI_TB_ROW_DEFINE)
    tmp["create_date"] = datetime.datetime.today()
    return tmp


def validate_device_row(row):
    return utils.validate_mongo_row(row, DEVICE_TB_ROW_DEFINE)


def validate_device_cols(**cols):
    return utils.validate_mongo_row_cols(DEVICE_TB_ROW_DEFINE, **cols)


def has_device_col(colname):
    return utils.has_mongo_row_col(DEVICE_TB_ROW_DEFINE, colname)
