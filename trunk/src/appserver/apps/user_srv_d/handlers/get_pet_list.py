# -*- coding: utf-8 -*-
#import json
#import urllib
import logging
#import traceback
from lib import error_codes

#from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

#from lib import utils
#from lib import sys_config
#from lib.sys_config import SysConfig


class GetPetList(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("GetPetList, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        #user_dao = self.settings["user_dao"]
        #device_dao = self.settings["device_dao"]
        #conf = self.settings["appconfig"]
        custom_headers = self.custom_headers()
        res = {"status": error_codes.EC_SUCCESS}

        uid = None
        token = None

        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
        except Exception, e:
            logging.warning("invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        try:
            st = yield self.check_token("OnGetPetList", res, uid, token)
            if not st:
               return
            res["list"] = []
            info = yield pet_dao.get_pet_list(uid, ("pet_id", "device_imei",
                                                     "nick","choice", "logo_url"))
            if not info:
                logging.warning("get pet list of uid:%d  not found, %s", uid, self.dump_req())
            else:
                for en in info:
                    res["list"].append(en)
        except Exception, e:
            logging.error(" error, %s %s", self.dump_req(),
                          self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

# 成功
        logging.debug(" success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()