# -*- coding: utf-8 -*-

import copy
import datetime

import pymongo
from pymongo.operations import IndexModel

from lib import utils

USER_DATABASE = "xmq_user"
"""
用户基本信息表
"""
USER_INFOS_TB = "user_infos"
USER_INFOS_TB_INDEXES = [
    IndexModel("uid", unique=True),
    IndexModel("phone_num", unique=True), IndexModel("register_date"),
    IndexModel("mod_date"), IndexModel("last_login_date")
]
_USER_INFOS_TB_ROW_DEFINE = {
    "uid": (None, int),  # 用户全局唯一ID
    "phone_num": (None, unicode),  # 手机号码
    "home_wifi": ({}, dict),
    "register_date": (None, datetime.datetime),
    "last_login_date": (None, datetime.datetime),
    "mod_date": (None, datetime.datetime),
}


def new_user_infos_row():
    tmp = utils.new_mongo_row(_USER_INFOS_TB_ROW_DEFINE)
    cur = datetime.datetime.today()
    tmp["register_date"] = cur
    tmp["last_login_date"] = cur
    tmp["mod_date"] = cur
    return tmp


def validate_user_infos_row(row):
    return utils.validate_mongo_row(row, _USER_INFOS_TB_ROW_DEFINE)


def validate_user_infos_cols(**cols):
    return utils.validate_mongo_row_cols(_USER_INFOS_TB_ROW_DEFINE, **cols)


def has_user_infos_col(colname):
    return utils.has_mongo_row_col(_USER_INFOS_TB_ROW_DEFINE, colname)


"""
用户登录状态
"""
USER_LOGIN_STATUS_TB = "user_login_status"
USER_LOGIN_STATUS_TB_INDEXES = [
    IndexModel("uid", unique=True),
    IndexModel("failed_count"),
]
_USER_LOGIN_STATUS_TB_ROW_DEFINE = {
    "uid": None,
    "token": None,
    "begin_date": None,
    "end_date": None,
    "failed_count": 0,
}


def new_user_login_status_row():
    tmp = copy.deepcopy(_USER_LOGIN_STATUS_TB_ROW_DEFINE)
    tmp["begin_date"] = datetime.datetime.today()
    return tmp
