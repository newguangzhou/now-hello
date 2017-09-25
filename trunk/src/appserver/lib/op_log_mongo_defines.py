# -*- coding: utf-8 -*-

import copy
import datetime

import pymongo
from pymongo.operations import IndexModel
import datetime
from lib import utils

OP_LOG_DATABASE = "xmq_op_log"
"""
操作日志
"""
OP_LOG_INFOS_TB = "op_log_info"
OP_LOG_INFOS_TB_INDEXES = [
    IndexModel("imei"),
    IndexModel("log_time"),
]
_OP_LOG_TB_ROW_DEFINE = {
    "imei": (u"", unicode),
    "log_time": (None, datetime.datetime),
    "content": (u"", unicode),
}


def new_op_log_row():
    tmp = utils.new_mongo_row(_OP_LOG_TB_ROW_DEFINE)
    tmp["log_time"] = datetime.datetime.today()
    return tmp


def validate_op_log_row(row):
    return utils.validate_mongo_row(row, _OP_LOG_TB_ROW_DEFINE)


def validate_op_log_cols(**cols):
    return utils.validate_mongo_row_cols(_OP_LOG_TB_ROW_DEFINE, **cols)


def has_op_log_col(colname):
    return utils.has_mongo_row_col(_OP_LOG_TB_ROW_DEFINE, colname)
