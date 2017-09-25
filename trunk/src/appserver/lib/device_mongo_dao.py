import threading
import logging
import time
import traceback
import random
import json
import bson

from tornado import ioloop, gen

import device_mongo_defines as device_def
import utils
import copy

from sys_config import SysConfig
import type_defines

import pymongo

from mongo_dao_base import MongoDAOBase


class DeviceMongoDAOException(Exception):
    def __init__(self, message, *args):
        self._msg = message % tuple(args)

    def __str__(self):
        return self._msg


class DeviceMongoDAO(MongoDAOBase):
    def __init__(self, *args, **kwargs):
        MongoDAOBase.__init__(self, *args, **kwargs)

    @gen.coroutine
    def add_device_info(self, **kwargs):
        device_info = kwargs

        def _callback(mongo_client, **kwargs):
            tb = mongo_client[device_def.DEVICE_DATABASE][
                device_def.DEVICE_INFOS_TB]

            row = device_def.new_device_infos_row()
            for (k, v) in device_info.items():
                if row.has_key(k):
                    row[k] = v
                else:
                    raise DeviceMongoDAOException(
                        "Unknwon device infos row column \"%s\"", k)

            validate_ret, exp_col = device_def.validate_device_infos_row(row)
            if not validate_ret:
                raise DeviceMongoDAOException(
                    "Validate device infos row failed, invalid column \"%s\"",
                    exp_col)
            tb.update_one({"imei": row["imei"]}, {"$set": row}, upsert=True)

        yield self.submit(_callback)

    @gen.coroutine
    def update_device_info(self, imei, **kwargs):
        info = kwargs
        validate_ret, exp_col = device_def.validate_device_infos_cols(**kwargs)
        if not validate_ret:
            raise DeviceMongoDAOException(
                "Validate device infos columns error, invalid column \"%s\"",
                exp_col)

        def _callback(mongo_client, **kwargs):
            tb = mongo_client[device_def.DEVICE_DATABASE][
                device_def.DEVICE_INFOS_TB]
            info["imei"] = imei
            res = tb.update_one({"imei": imei}, {"$set": info})
            return res

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def get_device_info(self, imei, cols):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[device_def.DEVICE_DATABASE][
                device_def.DEVICE_INFOS_TB]
            qcols = {"_id": 0}
            for v in cols:
                if not device_def.has_device_infos_col(v):
                    raise DeviceMongoDAOException(
                        "Unknown device infos row column \"%s\"", v)
                qcols[v] = 1

            cursor = tb.find({"imei": imei}, qcols)
            if cursor.count() <= 0:
                return None
            return cursor[0]

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def get_location_infos(self, imei):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[device_def.DEVICE_DATABASE][
                device_def.DEVICE_INFOS_TB]
            return tb.find({"imei": imei}, {"location_data": 1,
                                            "_id": 0},
                           sort=[("systemtimestamp", pymongo.DESCENDING)])

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def add_location_info(self, imei, location_info):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[device_def.DEVICE_DATABASE][
                device_def.DEVICE_INFOS_TB]
            row = device_def.new_device_infos_row()
            push_all_dict = {}
            if location_info:
                push_all_dict["location_data"] = location_info
            tb.update_one({"imei": imei}, {"$pushAll": push_all_dict},
                          upsert=True)

        yield self.submit(_callback)
