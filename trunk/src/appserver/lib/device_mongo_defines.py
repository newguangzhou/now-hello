# -*- coding: utf-8 -*-

import copy
import datetime

import pymongo
from pymongo.operations import IndexModel

from lib import utils

DEVICE_DATABASE = "xmq_device"
"""
追踪器基本信息表
"""
DEVICE_INFOS_TB = "device_infos"
DEVICE_INFOS_TB_INDEXES = [IndexModel("imei", unique=True), ]

_DEVICE_INFOS_TB_ROW_DEFINE = {
    "imei": (u"", unicode),  # 追踪器全局唯一ID
    "device_name": (u"", unicode),  #设备名称
    "iccid": (u"", unicode),
    "light_status": (0, int),
    "register_date": (None, datetime.datetime),
    "mod_date": (None, datetime.datetime),
    "setting": (u"", unicode),#保存设备配置信息
    "update_time": (None, datetime.datetime),#设备上一次更改配置的时间
    "location_data": ([], list)
}


def new_device_infos_row():
    tmp = utils.new_mongo_row(_DEVICE_INFOS_TB_ROW_DEFINE)
    cur = datetime.datetime.today()
    tmp["register_date"] = cur
    tmp["mod_date"] = cur
    tmp["update_time"] = cur
    return tmp


def validate_device_infos_row(row):
    return utils.validate_mongo_row(row, _DEVICE_INFOS_TB_ROW_DEFINE)


def validate_device_infos_cols(**cols):
    return utils.validate_mongo_row_cols(_DEVICE_INFOS_TB_ROW_DEFINE, **cols)


def has_device_infos_col(colname):
    return utils.has_mongo_row_col(_DEVICE_INFOS_TB_ROW_DEFINE, colname)


