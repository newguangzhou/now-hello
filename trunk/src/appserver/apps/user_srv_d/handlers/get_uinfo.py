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
from lib import utils
from helper_handler import HelperHandler

class GetUInfo(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnGetUInfo, %s", self.dump_req())
        
        self.set_header("Content-Type", "application/json; charset=utf-8")
        
        res = {"status":error_codes.EC_SUCCESS}
        user_dao = self.settings["user_dao"]
        conf = self.settings["appconfig"]
        
        # 获取请求参数
        uid = None 
        token = None
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
        except Exception,e:
            logging.warning("OnGetUInfo, invalid args, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return 
       
        # 
        try:
            # 检查账号状态
            st = yield self.check_account_status("OnGetUInfo", res, uid)
            if not st:
                return
            
            # 检查token
            st = yield self.check_token("OnGetUInfo", res, uid, token)
            if not st:
                return
            
            # 获取用户信息
            info = yield user_dao.get_user_info(uid, ("nick", "logo_url", "birthday", "sex", "xp", "jifen"))
            for (k,v) in info.items():
                if k == "birthday":
                    res[k] = utils.date2str(v, True)
                else:
                    res[k] = v
        except Exception,e:
            logging.warning("OnGetUInfo, error, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return 
    
        # 成功
        logging.debug("OnGetUInfo, success, %s", self.dump_req())
        self.res_and_fini(res)
        
    def post(self):
        return self._deal_request()
    
    def get(self):
        return self._deal_request()
    
    