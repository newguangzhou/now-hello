# -*- coding: utf-8 -*-

import tornado.web
import json
import hashlib
import random 
import time
import datetime

import logging
import traceback

from tornado.web import asynchronous
from tornado import gen

from lib import error_codes
from helper_handler import HelperHandler

import lib.utils

class UpdateUInfo(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnUpdateUInfo, %s", self.dump_req())
        
        self.set_header("Content-Type", "application/json; charset=utf-8")
        
        res = {"status":error_codes.EC_SUCCESS}
        user_dao = self.settings["user_dao"]
        conf = self.settings["appconfig"]
        
        # 获取请求参数
        uid = None 
        token = None
        nick = None 
        logo_url = None 
        sex = None
        birthday = None
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            
            if self.request.arguments.has_key("nick"):
                nick = self.decode_argument(self.get_argument("nick")).encode("utf8")
            if self.request.arguments.has_key("logo_url"):
                logo_url = self.decode_argument(self.get_argument("logo_url")).encode("utf8")
            if self.request.arguments.has_key("sex"):
                sex = int(self.get_argument("sex"))
                if sex != 1 and sex != 2 and sex != 0:
                    self.arg_error("sex")
            if self.request.arguments.has_key("birthday"):
                birthday = self.get_argument("birthday")
                birthday = lib.utils.str2date(birthday, "%Y-%m-%d")
                birthday = datetime.datetime(birthday.year, birthday.month, birthday.day)
            if not nick and not logo_url and not sex and not birthday:
                self.arg_error("All update props was not given")
        except Exception,e:
            logging.warning("OnUpdateUInfo, invalid args, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return 
        
        # 
        try:
            # 检查账号状态
            st = yield self.check_account_status("OnUpdateUInfo", res, uid)
            if not st:
                return
            
            # 检查token
            st = yield self.check_token("OnUpdateUInfo", res, uid, token)
            if not st: 
                return
            
            # 更新信息
            info = {"mod_date":datetime.datetime.today()}
            if nick:
                info["nick"] = nick 
            if logo_url:
                info["logo_url"] = logo_url
            if sex:
                info["sex"] = sex
            if birthday:
                info["birthday"] = birthday
        
            yield user_dao.update_user_info(uid, **info)
        except Exception,e:
            logging.warning("OnUpdateUInfo, error, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        
        # 成功
        logging.debug("OnUpdateUInfo, success, %s", self.dump_req())
        self.res_and_fini(res)
        
    def post(self):
        return self._deal_request()
    
    def get(self):
        return self._deal_request()
    
    