import threading
import logging
import time
import traceback
import random
import json
import bson

from tornado import ioloop, gen

import pet_mongo_defines as pet_def
import utils

from sys_config import SysConfig
import type_defines

import pymongo

from mongo_dao_base import MongoDAOBase


class PetMongoDAOException(Exception):
    def __init__(self, message, *args):
        self._msg = message % tuple(args)

    def __str__(self):
        return self._msg


class PetMongoDAO(MongoDAOBase):
    def __init__(self, *args, **kwargs):
        MongoDAOBase.__init__(self, *args, **kwargs)

    @gen.coroutine
    def add_pet_info(self,uid, **kwargs):
        pet_info = kwargs

        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_INFOS_TB]

            row = pet_def.new_pet_infos_row()
            for (k, v) in pet_info.items():
                if row.has_key(k):
                    row[k] = v
                else:
                    raise PetMongoDAOException(
                        "Unknwon pet infos row column \"%s\"", k)

            validate_ret, exp_col = pet_def.validate_pet_infos_row(row)
            if not validate_ret:
                raise PetMongoDAOException(
                    "Validate pet infos row failed, invalid column \"%s\"",
                    exp_col)

            # tb.insert_one(row)
            res = tb.update_one({"uid": uid}, {"$set": row},
                                upsert=True)

        yield self.submit(_callback)

    @gen.coroutine
    def update_pet_info(self, pet_id, **kwargs):
        info = kwargs
        #validate_ret, exp_col = pet_def.validate_pet_infos_cols(**kwargs)
        #if not validate_ret:
        #    raise PetMongoDAOException(
        #        "Validate pet infos columns error, invalid column \"%s\"",
        #        exp_col)

        info["pet_id"] = pet_id

        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_INFOS_TB]
            res = tb.update_one({"pet_id": pet_id}, {"$set": info},
                                upsert=True)
            return res.modified_count

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def update_pet_info_by_uid(self, uid, **kwargs):
        info = kwargs
        # validate_ret, exp_col = pet_def.validate_pet_infos_cols(**kwargs)
        # if not validate_ret:
        #    raise PetMongoDAOException(
        #        "Validate pet infos columns error, invalid column \"%s\"",
        #        exp_col)

        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_INFOS_TB]
            res = tb.update_one({"uid": uid}, {"$set": info},
                                upsert=True)
            return res.modified_count

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def unbind_device_imei(self, pet_id):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_INFOS_TB]
            res = tb.delete_one({"pet_id": pet_id})

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def get_user_pets(self, uid, cols):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_INFOS_TB]
            qcols = {"_id": 0}
            for v in cols:
                if not pet_def.has_pet_infos_col(v):
                    raise PetMongoDAOException(
                        "Unknown pet infos row column \"%s\"", v)
                qcols[v] = 1

            cursor = tb.find({"uid": uid}, qcols)
            if cursor.count() <= 0:
                return None
            return cursor[0]

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    # @gen.coroutine
    # def get_pet_info(self, pet_id, cols, device_imei=None):
    #     def _callback(mongo_client, **kwargs):
    #         tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_INFOS_TB]
    #         qcols = {"_id": 0}
    #         for v in cols:
    #             if not pet_def.has_pet_infos_col(v):
    #                 raise PetMongoDAOException(
    #                     "Unknown pet infos row column \"%s\"", v)
    #             qcols[v] = 1
    #         cond = {}
    #         if pet_id is not None:
    #             cond["pet_id"] = pet_id
    #         if device_imei is not None:
    #             cond["device_imei"] = device_imei
    #         cursor = tb.find(cond, qcols)
    #         if cursor.count() <= 0:
    #             return None
    #         return cursor[0]
    #
    #     ret = yield self.submit(_callback)
    #     raise gen.Return(ret)

    @gen.coroutine
    def get_pet_info(self, cols, **kwargs):
        cond = kwargs

        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_INFOS_TB]
            qcols = {"_id": 0}
            for v in cols:
                if not pet_def.has_pet_infos_col(v):
                    raise PetMongoDAOException(
                        "Unknown pet infos row column \"%s\"", v)
                qcols[v] = 1
            cursor = tb.find(cond, qcols)
            if cursor.count() <= 0:
                return None
            return cursor[0]

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def bind_device(self, uid, imei, pet_id):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_INFOS_TB]
            # res = tb.insert_one({"uid": uid,"device_imei": imei,"pet_id":pet_id})
            info={"device_imei": imei,"pet_id":pet_id}
            res=tb.update_one({"uid": uid}, {"$set": info},
                       upsert=True)
            return res

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def is_pet_id_exist(self, pet_id, uid):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_INFOS_TB]
            cursor = tb.find({"pet_id": pet_id,
                              "uid": uid}, {"_id": 0,
                                            "pet_id": 1})
            return cursor.count() > 0

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def get_location_infos(self, pet_id):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][
                pet_def.PET_LOCATION_INFOS_TB]
            qcols = {"_id": 0}
            cursor = tb.find({"pet_id": pet_id}, qcols)
            if cursor.count() <= 0:
                return None
            return cursor

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def add_location_info(self, pet_id, device_imei, location_info):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][
                pet_def.PET_LOCATION_INFOS_TB]
            row = pet_def.new_pet_location_row()
            for (k, v) in location_info.items():
                if row.has_key(k):
                    row[k] = v
                else:
                    raise PetMongoDAOException(
                        "Unknwon pet infos row column \"%s\"", k)
            row["pet_id"] = pet_id
            row["device_imei"] = device_imei

            tb.insert_one(row)

        yield self.submit(_callback)

    @gen.coroutine
    def add_sport_info(self, pet_id, imei, sport_data):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_SPORT_INFOS_TB]
            row = pet_def.new_pet_sport_row()
            row["device_imei"] = imei
            row["pet_id"] = pet_id
            row["diary"] = sport_data["diary"]
            row["step_count"] = sport_data["step_count"]
            row["distance"] = sport_data["distance"]
            row["calorie"] = sport_data["calorie"]
            row["target_energy"] = sport_data["target_energy"]
            tb.update_one({"pet_id": pet_id,
                           "diary": sport_data["diary"]}, {"$set": row},
                          upsert=True)

        yield self.submit(_callback)

    @gen.coroutine
    def get_sport_info(self, pet_id, start_time, end_time):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_SPORT_INFOS_TB]
            qcols = {"_id": 0}
            find_cond = {"pet_id": pet_id, "diary": {"$gte": start_time}}
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
    def add_sleep_info(self, pet_id, imei, sleep_data):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_SLEEP_INFOS_TB]
            rows = []
            for item in sleep_data:
                row = pet_def.new_pet_sleep_row()
                row["device_imei"] = imei
                row["pet_id"] = pet_id
                row["begin_time"] = item["begin_time"]
                row["total_secs"] = item["total_secs"]
                row["quality"] = item["quality"]
                rows.append(row)
            tb.insert(rows)

        yield self.submit(_callback)

    @gen.coroutine
    def get_sleep_info(self, pet_id, start_time, end_time):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_SLEEP_INFOS_TB]
            qcols = {"_id": 0}
            find_cond = {"pet_id": pet_id, "begin_time": {"$gte": start_time}}
            if end_time != None:
                find_cond["begin_time"]["$lte"] = end_time
            cursor = tb.find(find_cond, qcols)
            if cursor.count() <= 0:
                return None
            return cursor

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def add_common_wifi_info(self, pet_id, common_wifi_info):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_INFOS_TB]
            tb.update_one({"pet_id": pet_id}, {"$set": {"common_wifi":common_wifi_info}})

        yield self.submit(_callback)

    @gen.coroutine
    def set_home_wifi(self, uid, home_wifi):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_INFOS_TB]
            res = tb.update_one({"uid": uid},
                                {"$set": {"home_wifi": home_wifi,"common_wifi":[]}})
            return res

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def set_home_location(self, uid, home_location):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[pet_def.PET_DATABASE][pet_def.PET_INFOS_TB]
            res = tb.update_one({"uid": uid},
                                {"$set": {"home_location": home_location}})
            return res

        ret = yield self.submit(_callback)
        raise gen.Return(ret)
