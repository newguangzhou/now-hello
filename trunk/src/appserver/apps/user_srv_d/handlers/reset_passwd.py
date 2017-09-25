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

class ResetPasswd(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnResetPasswd, %s", self.dump_req())
        
        self.set_header("Content-Type", "application/json; charset=utf-8")
        
        auth_dao = self.settings["auth_dao"]
        conf = self.settings["appconfig"]
        
        res = {"status":error_codes.EC_SUCCESS}
        
        # 获取请求参数
        phone_num = None 
        code = None
        new_passwd = None
        try:
            phone_num = self.get_argument("phone_num")
            code = self.get_argument("code")
            new_passwd = self.get_argument("new_pass")
        except Exception,e:
            logging.warning("OnResetPasswd, invalid args, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return 
        
        #
        try:
            uid = yield self.check_account_exist_by_phone_num("OnResetPasswd", res, phone_num)
            if not uid:
                return 
            
            st = yield self.check_verify_code("OnResetPasswd", res, 3, phone_num, code)
            if not st:
                return
            
            yield auth_dao.update_user_passwd(phone_num, new_passwd)
            
            yield auth_dao.delete_user_all_tokens(uid)
        except Exception,e:
            logging.error("OnResetPasswd, error, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
            
        # 成功
        logging.debug("OnResetPasswd, success %s",  self.dump_req())
        self.res_and_fini(res)
    
    def post(self):
        return self._deal_request()
    
    def get(self):
        return self._deal_request()
    