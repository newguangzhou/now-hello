# -*- coding: utf-8 -*-

import threading
import logging 
import time
import traceback
import random
import json
import bson

from tornado import ioloop, gen

import user_mongo_defines as user_def
import utils

from sys_config import SysConfig
import type_defines

import pymongo

from mongo_dao_base import MongoDAOBase

class UserMongoDAOException(Exception):
    def __init__(self, message, *args):
        self._msg = message % tuple(args)
    
    def __str__(self):
        return self._msg

class UserMongoDAO(MongoDAOBase):
    def __init__(self, *args, **kwargs):
        MongoDAOBase.__init__(self, *args, **kwargs)
    
    @gen.coroutine
    def add_user_info(self, **kwargs):
        user_info = kwargs 
        
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[user_def.USER_DATABASE][user_def.USER_INFOS_TB]
            
            row = user_def.new_user_infos_row()
            for (k,v) in user_info.items():
                if row.has_key(k):
                    row[k] = v
                else:
                    raise UserMongoDAOException("Unknwon user infos row column \"%s\"", k)
            
            validate_ret, exp_col = user_def.validate_user_infos_row(row)
            if not validate_ret:
                raise UserMongoDAOException("Validate user infos row failed, invalid column \"%s\"", exp_col)
            
            tb.insert_one(row)
        
        yield self.submit(_callback)
    
    @gen.coroutine
    def update_user_info(self, uid, **kwargs):
        info = kwargs
        validate_ret, exp_col = user_def.validate_user_infos_cols(**kwargs)
        if not validate_ret:
            raise UserMongoDAOException("Validate user infos columns error, invalid column \"%s\"", exp_col)
        
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[user_def.USER_DATABASE][user_def.USER_INFOS_TB]
            if info.has_key("uid"):
                del info["uid"]
            
            res = tb.update_one({"uid":uid}, {"$set":info})
            return res.modified_count
        
        ret = yield self.submit(_callback)
        raise gen.Return(ret) 
    
    @gen.coroutine
    def inc_user_jifen(self, uid, jifen):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[user_def.USER_DATABASE][user_def.USER_INFOS_TB]
            res = tb.update_one({"uid":uid}, {"$inc":{"jifen":jifen}})
            if not res.modified_count:
                raise UserMongoDAOException("Inc user jifen error, not found, uid=%u", uid)
        
        yield self.submit(_callback)
    
    @gen.coroutine
    def is_user_info_exists(self, uid):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[user_def.USER_DATABASE][user_def.USER_INFOS_TB]
            return tb.count({"uid":uid}) > 0
        
        ret = yield self.submit(_callback)
        raise gen.Return(ret)
    
    @gen.coroutine
    def is_user_info_exists_by_phone_num(self, phone_num):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[user_def.USER_DATABASE][user_def.USER_INFOS_TB]
            return tb.count({"phone_num":phone_num}) > 0
        
        ret = yield self.submit(_callback)
        raise gen.Return(ret)
    
    @gen.coroutine
    def get_user_info(self, uid, cols):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[user_def.USER_DATABASE][user_def.USER_INFOS_TB]
            qcols = {"_id":0}
            for v in cols: 
                if not user_def.has_user_infos_col(v):
                    raise UserMongoDAOException("Unknown user infos row column \"%s\"", v)
                qcols[v] = 1
            
            cursor = tb.find({"uid":uid}, qcols)
            if cursor.count() <= 0:
                return None 
            
            dc = cursor[0]
            if dc.has_key("logo_url") and dc["logo_url"]:
                dc["logo_url"] = SysConfig.current().gen_file_url(type_defines.USER_LOGO_FILE, dc["logo_url"])
            
            return dc
        
        ret = yield self.submit(_callback)
        raise gen.Return(ret) 

    @gen.coroutine
    def set_home_wifi(self, uid, home_wifi):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[user_def.USER_DATABASE][user_def.USER_INFOS_TB]
            res = tb.update_one({"uid":uid}, {"$set":{"home_wifi":home_wifi}})
            return res
        
        ret = yield self.submit(_callback)
        raise gen.Return(ret) 
    
