import bson

from tornado import ioloop, gen
import datetime

import new_device_mongo_defines as new_device_def
import utils
import copy

from sys_config import SysConfig
import type_defines

import pymongo

from mongo_dao_base import MongoDAOBase


class NewDeviceMongoDAOException(Exception):
    def __init__(self, message, *args):
        self._msg = message % tuple(args)

    def __str__(self):
        return self._msg


class NewDeviceMongoDAO(MongoDAOBase):
    def __init__(self, *args, **kwargs):
        MongoDAOBase.__init__(self, *args, **kwargs)

    @gen.coroutine
    def add_healthy_info(self, imei, sleep_data):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_SLEEP_INFOS_TB]
            rows = []
            for item in sleep_data:
                row = new_device_def.new_device_sleep_row()
                row["imei"] = imei
                row["begin_time"] = item["begin_time"]
                row["total_secs"] = item["total_secs"]
                row["quality"] = item["quality"]
                rows.append(row)
            tb.insert(rows)

        yield self.submit(_callback)

    @gen.coroutine
    def get_healthy_info(self, imei, start_time, end_time):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_SLEEP_INFOS_TB]
            qcols = {"_id": 0}
            find_cond = {"imei": imei, "begin_time": {"$gte": start_time}}
            if end_time != None:
                find_cond["begin_time"]["$lte"] = end_time
            cursor = tb.find(find_cond, qcols)
            if cursor.count() <= 0:
                return None
            return cursor

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def add_sport_info(self, imei, sport_data):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_SPORT_INFOS_TB]
            row = new_device_def.new_device_sport_row()
            row["imei"] = imei
            row["diary"] = sport_data["diary"]
            row["step_count"] = sport_data["step_count"]
            row["distance"] = sport_data["distance"]
            row["calorie"] = sport_data["calorie"]
            tb.update_one({"imei": imei,
                           "diary": sport_data["diary"]}, {"$set": row},
                          upsert=True)

        yield self.submit(_callback)

    @gen.coroutine
    def get_sport_info(self, imei, start_time, end_time):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_SPORT_INFOS_TB]
            qcols = {"_id": 0}
            find_cond = {"imei": imei, "diary": {"$gte": start_time}}
            if end_time != None:
                find_cond["diary"]["$lte"] = end_time
            #print find_cond
            cursor = tb.find(find_cond, qcols)
            #print cursor.count()
            if cursor.count() <= 0:
                return None
            return cursor

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def add_terminal_log(self, imei, log_items):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_INFOS_TB]
            push_all_dict = {}
            if log_items:
                push_all_dict["log_items"] = log_items
            tb.update_one({"imei": imei}, {"$pushAll": push_all_dict},
                          upsert=True)

        yield self.submit(_callback)

    @gen.coroutine
    def update_device_info(self, imei, **kwargs):
        device_info = kwargs
        print "update_device_info:", device_info
        validate_ret, exp_col = new_device_def.validate_device_cols(**kwargs)
        if not validate_ret:
            raise NewDeviceMongoDAOException(
                "Validate device infos columns error, invalid column \"%s\"",
                exp_col)

        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_INFOS_TB]
            device_info["imei"] = imei
            tb.update_one({"imei": imei}, {"$set": device_info}, upsert=True)

        yield self.submit(_callback)


    @gen.coroutine
    def unbind_device_imei(self, imei):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][new_device_def.DEVICE_INFOS_TB]
            tb.delete_one({"imei": imei})

        yield self.submit(_callback)

# @gen.coroutine
# def add_device_info(self, **kwargs):
#     return

    @gen.coroutine
    def get_device_info_by_uid(self, uid, cols):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_INFOS_TB]
            qcols = {"_id": 0}
            for v in cols:
                if not new_device_def.has_device_col(v):
                    raise NewDeviceMongoDAOException(
                        "Unknown device infos row column \"%s\"", v)
                qcols[v] = 1

            cursor = tb.find({"uid": uid}, qcols)
            if cursor.count() <= 0:
                return None
            return cursor[0]

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def get_device_info(self, imei, cols):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_INFOS_TB]
            qcols = {"_id": 0}
            for v in cols:
                if not new_device_def.has_device_col(v):
                    raise NewDeviceMongoDAOException(
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
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_INFOS_TB]
            qcols = {"location_data": 1, "_id": 0}
            cursor = tb.find({"imei": imei}, qcols)
            if cursor.count() <= 0:
                return None
            return cursor[0]

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def add_location_info(self, imei, location_info):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_INFOS_TB]
            push_all_dict = {}
            if location_info:
                push_all_dict["location_data"] = location_info
            tb.update_one({"imei": imei}, {"$push": push_all_dict},
                          upsert=True)

        yield self.submit(_callback)

    @gen.coroutine
    def report_wifi_info(self, imei, wifi_info):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_WIFI_INFOS_TB]
            row = new_device_def.new_device_wifi_row()
            row["imei"] = imei
            row["wifi_info"] = wifi_info
            tb.insert_one(row)

        yield self.submit(_callback)

    @gen.coroutine
    def get_last_wifi_info(self, imei):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_WIFI_INFOS_TB]
            qcols = {"_id": 0}
            cursor = tb.find({"imei": imei},
                             qcols,
                             sort=[("create_date", pymongo.DESCENDING)])
            if cursor.count() <= 0:
                return None
            return cursor[0]

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def get_ten_minutes_wifi_info(self, imei):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_WIFI_INFOS_TB]
            now_time = datetime.datetime.now();
            pre_ten_minutes_time = now_time + datetime.timedelta(minutes=-10)
            qcols = {"_id": 0}
            cursor = tb.find({"imei": imei,
                              "create_date": {"$gte": pre_ten_minutes_time, "$lt": now_time}},
                             qcols)
            if cursor.count() <= 0:
                return None
            return cursor

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def get_arround_ten_minutes_wifi_info(self, imei,that_time):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[new_device_def.DEVICE_DATABASE][
                new_device_def.DEVICE_WIFI_INFOS_TB]
            # now_time = datetime.datetime.now();
            pre_ten_minutes_time = that_time + datetime.timedelta(minutes=-10)
            aft_ten_minutes_time= that_time + datetime.timedelta(minutes=10)
            qcols = {"_id": 0}
            cursor = tb.find({"imei": imei,
                              "create_date": {"$gte": pre_ten_minutes_time, "$lt": aft_ten_minutes_time}},
                             qcols)
            if cursor.count() <= 0:
                return None
            return cursor

        ret = yield self.submit(_callback)
        raise gen.Return(ret)