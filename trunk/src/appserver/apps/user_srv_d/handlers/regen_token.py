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
from lib import sys_config
from lib.sys_config import SysConfig

from helper_handler import HelperHandler

class RegenToken(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnRegenToken, %s", self.dump_req())
        
        self.set_header("Content-Type", "application/json; charset=utf-8")
        custom_headers = self.custom_headers()
        auth_dao = self.settings["auth_dao"]
        conf = self.settings["appconfig"]
        
        res = {"status":error_codes.EC_SUCCESS}
        
        # 获取请求参数
        uid = None
        token = None
        device_type = None
        device_token = None
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            device_type = int(self.get_argument("device_type"))
            if device_type not in (1, 2):
                self.arg_error("device_type")
            device_token = self.get_argument("device_token")
        except Exception,e:
            logging.warning("OnRegenToken, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return 
        
        #
        try:
            st = yield self.check_token("OnRegenToken", res, uid, token)
            if not st:
                return 
            
            yield auth_dao.delete_user_token(uid, token)
            
            new_token = yield auth_dao.gen_user_token(uid, True, device_type, device_token,
                                                      SysConfig.current().get(sys_config.SC_TOKEN_EXPIRE_SECS),
                                                      custom_headers["platform"], custom_headers["device_model"],custom_headers.get("x_os_int",23))

            res["new_token"] = new_token
            res["token_expire_secs"] = SysConfig.current().get(sys_config.SC_TOKEN_EXPIRE_SECS)
        except Exception,e:
            logging.error("OnRegenToken, error, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
            
        # 成功
        logging.debug("OnRegenToken, success %s",  self.dump_req())
        self.res_and_fini(res)
    
    def post(self):
        return self._deal_request()
    
    def get(self):
        return self._deal_request()
    