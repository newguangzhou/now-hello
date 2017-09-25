# -*- coding: utf-8 -*-
import json
import urllib
import logging
import datetime
import traceback
from lib import error_codes

from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

from lib import utils
from lib import sys_config
from lib.sys_config import SysConfig



class SetSimInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("SetSimInfo, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        device_dao = self.settings["device_dao"]
        conf = self.settings["appconfig"]
        res = {"status":error_codes.EC_SUCCESS}

        uid = None
        iccid = None
        device_imei = None


        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            st = yield self.check_token("SetSimInfo", res, uid, token)
            if not st:
               return
 
            device_imei = self.get_argument("imei")
            iccid = self.get_argument("iccid")
        except Exception, e:
            logging.warning("SetSimInfo, invalid args, %s %s", self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        
        try:
            update_res = yield device_dao.update_device_info(device_imei, iccid=iccid)
            #print update_res.matched_count, update_res.modified_count
            if update_res.matched_count <=0:
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return

        except Exception, e:
            logging.warning("SetSimInfo, sys error, %s %s", self.dump_req(), str(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return


   # 成功
        logging.debug("SetSimInfo, success %s",  self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
