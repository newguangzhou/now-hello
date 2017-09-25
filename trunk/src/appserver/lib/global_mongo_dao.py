# -*- coding: utf-8 -*-

import threading
import logging 
import time
import traceback
import random
import json
import bson

from tornado import ioloop, gen
import haversine

import global_mongo_defines as global_def
import utils

import pymongo
import type_defines 

from mongo_dao_base import MongoDAOBase

class GlobalMongoDAOException(Exception):
    def __init__(self, message, *args):
        self._msg = message % tuple(args)
    
    def __str__(self):
        return self._msg

class GlobalMongoDAO(MongoDAOBase):
    def __init__(self, *args, **kwargs):
        MongoDAOBase.__init__(self, *args, **kwargs)
        
        
    @gen.coroutine
    def get_sys_config_item(self, category, key):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[global_def.GLOBAL_DATABASE][global_def.SYS_CONFIG_TB]
            cursor = tb.find({"category":category, "key":key}, {"_id":0, "value":1})
            if cursor.count() <= 0:
                return None
            else:
                return cursor[0]["value"]
        ret = yield self.submit(_callback)
        raise gen.Return(ret)
    
    @gen.coroutine
    def add_sys_config_item(self, category, key, value):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[global_def.GLOBAL_DATABASE][global_def.SYS_CONFIG_TB]
            row = global_def.new_sys_config_row()
            row["category"] = category
            row["key"] = key
            row["value"] = value
            tb.insert_one(row)
        
        yield self.submit(_callback)
        raise gen.Return(ret)
    
    @gen.coroutine
    def update_sys_config_item(self, category, key, value):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[global_def.GLOBAL_DATABASE][global_def.SYS_CONFIG_TB]
            res = tb.update_one({"category":category, "key":key}, {"$set":{"value":value}})
            return res.modified_count
        
        ret = yield self.submit(_callback)
        raise gen.Return(ret)
    
    @gen.coroutine
    def set_sys_config_item(self, category, key, value):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[global_def.GLOBAL_DATABASE][global_def.SYS_CONFIG_TB]
            
            if tb.find({"category":category, "key":key}, {"_id":0, "key":1}).count() > 0:
                res = tb.update_one({"category":category, "key":key}, {"$set":{"value":value}})
                return res.modified_count > 0
            else:
                row = global_def.new_sys_config_row()
                row["category"] = category
                row["key"] = key
                row["value"] = value
                tb.insert_one(row)
                return True
        ret = yield self.submit(_callback)
        raise gen.Return(ret)
    
    @gen.coroutine
    def get_all_sys_config_items(self, category):
        def _callback(mongo_client, **kwargs):
            ret = {}
            tb = mongo_client[global_def.GLOBAL_DATABASE][global_def.SYS_CONFIG_TB]
            cursor = tb.find({"category":category}, {"_id":0, "key":1, "value":1})
            for dc in cursor:
                ret[dc["key"]] = dc["value"]
            return ret
        
        ret = yield self.submit(_callback)
        raise gen.Return(ret)
    
    @gen.coroutine
    def alloc_gid(self, type, owner):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[global_def.GLOBAL_DATABASE][global_def.GID_ALLOC_STATUS_TB]
            cursor = tb.find({"type":type, "owner":owner})
            if cursor.count() <= 0:
                raise GlobalMongoDAOException("Can not alloc gid, not found, type=%u owner=\"%s\"", type, owner)
            status = cursor[0]
            
            if status["cur_alloc"] >= status["range_end"]:
                raise GlobalMongoDAOException("Can not alloc gid, range is overflow, type=%u owner=%s range_begin=%u range_end=%u",
                    type, owner, status["range_begin"], status["range_end"])
            
            ret = 0
            if status["cur_alloc"] == 0:
                ret = status["range_begin"]
            else:
                ret = status["cur_alloc"] + 1
            
            res = tb.update_one({"type":type, "owner":owner}, {"$set":{"cur_alloc":ret}})
            if res.modified_count != 1:
                raise GlobalMongoDAOException("Can not alloc gid, update alloc status error, type=%u owner=%s", type, owner)
            
            return ret
        
        ret = yield self.submit(_callback)
        raise gen.Return(ret)
    
    @gen.coroutine
    def alloc_user_gid(self, owner):
        ret = yield self.alloc_gid(type_defines.USER_GID, owner)
        raise gen.Return(ret)
    
    @gen.coroutine
    def alloc_audit_gid(self, owner):
        ret = yield self.alloc_gid(type_defines.AUDIT_GID, owner)
        raise gen.Return(ret) 
    
    
    
        
    
