import time
import traceback
import random
import json
import bson

from tornado import ioloop, gen

import op_log_mongo_defines as op_log_def
import utils

from sys_config import SysConfig
import type_defines

import pymongo

from mongo_dao_base import MongoDAOBase


class OpLogMongoDAOException(Exception):
    def __init__(self, message, *args):
        self._msg = message % tuple(args)

    def __str__(self):
        return self._msg


class OpLogMongoDAO(MongoDAOBase):
    def __init__(self, *args, **kwargs):
        MongoDAOBase.__init__(self, *args, **kwargs)

    @gen.coroutine
    def add_op_info(self, **kwargs):
        op_log_info = kwargs

        def _callback(mongo_client, **kwargs):
            tb = mongo_client[op_log_def.OP_LOG_DATABASE][
                op_log_def.OP_LOG_INFOS_TB]

            row = op_log_def.new_op_log_row()
            for (k, v) in op_log_info.items():
                if row.has_key(k):
                    row[k] = v
                else:
                    raise OpLogMongoDAOException(
                        "Unknwon  op log row column \"%s\"", k)

            validate_ret, exp_col = op_log_def.validate_op_log_row(row)
            if not validate_ret:
                raise OpLogMongoDAOException(
                    "Validate op log infos row failed, invalid column \"%s\"",
                    exp_col)

            tb.insert_one(row)

        yield self.submit(_callback)

    @gen.coroutine
    def get_log_info(self, start_date, end_date, imei, cols):
        def _callback(mongo_client, **kwargs):
            ret = []
            tb = mongo_client[op_log_def.OP_LOG_DATABASE][
                op_log_def.OP_LOG_INFOS_TB]
            qcols = {"_id": 0}
            for v in cols:
                if not op_log_def.has_op_log_col(v):
                    raise OpLogMongoDAOException(
                        "Unknown op log infos row column \"%s\"", v)
                qcols[v] = 1

            find_cond = {"imei": imei, "log_time": {"$gte": start_date}}
            if end_date != None:
                find_cond["log_time"]["$lte"]=end_date

            cursor = tb.find(find_cond, qcols).sort("log_time",
                                                    pymongo.DESCENDING)
            return cursor

        #print "caossdasdasdas", start_date, end_date, imei
        ret = yield self.submit(_callback)
        raise gen.Return(ret)
