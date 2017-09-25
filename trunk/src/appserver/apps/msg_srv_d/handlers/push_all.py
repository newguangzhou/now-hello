# -*- coding: utf-8 -*-

import tornado.web
import json
import hashlib
import random 
import time

import logging
import traceback

from tornado.web import asynchronous
from tornado import gen

from lib import error_codes
from lib import xmq_web_handler
from lib import type_defines

class PushAll(xmq_web_handler.XMQWebHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnPushAll, %s", self.dump_req())
        
        self.set_header("Content-Type", "application/json; charset=utf-8")
        
        res = {"status":error_codes.EC_SUCCESS}
        conf = self.settings["appconfig"]
        xiaomi_push = self.settings["xiaomi_push"]
        
        # 获取请求参数
        title = None
        desc = None
        data = ""
        try:    
            if self.request.arguments.has_key("title"):
                title = self.get_str_arg("title")
            else:
                title = conf.default_push_title
            
            if self.request.arguments.has_key("data"):
                data = self.get_str_arg("data")
                
            desc = self.get_str_arg("desc")
        except Exception,e:
            logging.warning("OnPushAll, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return 
            
        #
        try:
            and_msg = xiaomi_push.build_android_noti_msg(title, desc, None, data)
            ios_msg = xiaomi_push.build_ios_noti_msg(desc)
            
            yield xiaomi_push.push_all(and_msg)
            yield xiaomi_push.push_all(ios_msg)
        except Exception,e:
            logging.warning("OnPushAll, failed, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return 
        
        # 发送成功
        logging.debug("OnPushAll, success, %s", self.dump_req())
        self.res_and_fini(res)
        
    def post(self):
        return self._deal_request()
    
    def get(self):
        return self._deal_request()
    
    