# -*- coding: utf-8 -*-

import json
import urllib
import logging
import traceback
from lib import error_codes

from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

class SwitchLight(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnSwitchLight, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        device_dao = self.settings["device_dao"]
        uid = None
        token = None
        imei = None
        light_status = None
        res = {"status": error_codes.EC_SUCCESS}
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            imei = self.get_argument("imei")
            light_status = int(self.get_argument("light_status"))
        except Exception, e:
            logging.warning("OnSwitchLight, invalid args, %s, exception %s", self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        if light_status not in (1, 0):
            logging.warning("OnSwitchLight, invalid args, %s, exception %s", self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        # 检查token
        #st = yield self.check_token("OnSwitchLight", res, uid, token)
        #if not st:
        #    return

        try:
            info = yield pet_dao.get_user_pets(uid, ("pet_id","device_imei"))
            if info is None :
                logging.warning("OnSwitchLight, pet_id not found, %s", self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            if info["device_imei"] is None or (info["device_imei"]!=imei):
                logging.warning("OnSwitchLight, imei not found, %s", self.dump_req())
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return
            
        except Exception, e:
            logging.warning("OnSwitchLight, sys_error, %s, exception %s", self.dump_req(), str(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        
        
        try:
            update_res = yield device_dao.update_device_info(imei, light_status=light_status)
            #print update_res.matched_count, update_res.modified_count
            if update_res.matched_count <=0:
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return
        except Exception, e:
            logging.warning("OnSwitchLight, sys error, %s %s", self.dump_req(), str(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
