# -*- coding: utf-8 -*-

import tornado.web
import json
import urllib

import logging
import traceback

from tornado.web import asynchronous
from tornado import gen
from tornado.httpclient import AsyncHTTPClient 

from lib import error_codes
from lib import utils

from helper_handler import HelperHandler

class Logout(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnLogout, %s", self.dump_req())
        
        self.set_header("Content-Type", "application/json; charset=utf-8")
        
        auth_dao = self.settings["auth_dao"]
        conf = self.settings["appconfig"]
        
        res = {"status":error_codes.EC_SUCCESS}
        
        # 获取请求参数
        uid = None
        token = None
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
        except Exception,e:
            logging.warning("OnLogout, invalid args, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return 
        
        #
        try:
            st = yield self.check_token("OnLogout", res, uid, token)
            if not st:
                return 
            
            yield auth_dao.delete_user_token(uid, token)
        except Exception,e:
            logging.error("OnLogout, error, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
            
        # 成功
        logging.debug("OnLogout, success %s",  self.dump_req())
        self.res_and_fini(res)
    
    def post(self):
        return self._deal_request()
    
    def get(self):
        return self._deal_request()