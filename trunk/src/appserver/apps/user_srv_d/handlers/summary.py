# -*- coding: utf-8 -*-
import json
import urllib
import logging
import traceback
from lib import error_codes

from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

from lib import utils
from lib import sys_config
from lib.sys_config import SysConfig


class Summary(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("Summary, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        conf = self.settings["appconfig"]
        
        res = {"status":error_codes.EC_SUCCESS}

        uid = None
        token = None
        pet_id = -1

        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            st = yield self.check_token("GetSleepInfo", res, uid, token)
            if not st:
                return
            
            pet_id = int(self.get_argument("pet_id", -1))
        except Exception, e:
            logging.warning("Summary, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        res["activity_summary"] = "活动总结"
        res["sleep_summary"] = "睡眠总结"
        res["expert_remind"] = "专家提醒"

         # 成功
        logging.debug("Summary, success %s",  self.dump_req())
        self.res_and_fini(res)
    
    def post(self):
        return self._deal_request()
    
    def get(self):
        return self._deal_request()