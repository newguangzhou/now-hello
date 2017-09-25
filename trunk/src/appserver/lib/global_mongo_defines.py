# -*- coding: utf-8 -*-

import copy
import datetime

import pymongo
from pymongo.operations import IndexModel

GLOBAL_DATABASE = "xmq_global"

"""
系统配置表
"""
SYS_CONFIG_TB = "sys_config"
SYS_CONFIG_TB_INDEXES = [
    IndexModel([("category", pymongo.ASCENDING), ("key", pymongo.ASCENDING)], unique = True)
    ]
_SYS_CONFIG_TB_ROW_DEFINE = {
    "category":None,
    "key":None,
    "value":None,
    "add_date":None,
    "mod_date":None
    }
def new_sys_config_row():
    tmp = copy.deepcopy(_SYS_CONFIG_TB_ROW_DEFINE)
    cur = datetime.datetime.today()
    tmp["add_date"] = cur
    tmp["mod_date"] = cur
    return tmp

"""
全局唯一ID分配状态表
"""
GID_ALLOC_STATUS_TB = "gid_alloc_status"
GID_ALLOC_STATUS_TB_INDEXES = [
    IndexModel([("type", pymongo.ASCENDING), ("range_begin", pymongo.ASCENDING), ("range_end", pymongo.ASCENDING)], unique = True),
    IndexModel([("type", pymongo.ASCENDING), ("owner", pymongo.ASCENDING)], unique = True)
    ]
_GID_ALLOC_STATUS_TB_ROW_DEFINE = {
    "type":None,                            # 类型
    "range_begin":None,                     # 范围起始
    "range_end":None,                       # 范围结束
    "cur_alloc":None,                       # 当前分配的值是多少
    "owner":None,                           # 拥有者
    }
def new_gid_alloc_status_row():
    tmp = copy.deepcopy(_GID_ALLOC_STATUS_TB_ROW_DEFINE)
    return tmp

