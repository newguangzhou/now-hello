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


class GetDeviceSwitchLightStatus(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnGetDeviceSwitchLightStatus, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        device_dao = self.settings["device_dao"]
        conf = self.settings["appconfig"]

        res = {"status": error_codes.EC_SUCCESS}
        uid = None
        token = None
        device_imei = None

        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            device_imei = self.get_argument("imei", None)
        except Exception, e:
            logging.warning("OnGetDeviceSwitchLightStatus, invalid args, %s",
                            self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        try:
            st = yield self.check_token("OnGetSwitchLightStatus", res, uid, token)
            if not st:
               return
            if device_imei is None:
                info = yield pet_dao.get_user_pets(uid, ("device_imei", ))
                if not info:
                    logging.warning(
                        "OnGetDeviceSwitchLightStatus, not found, %s",
                        self.dump_req())
                    res["status"] = error_codes.EC_PET_NOT_EXIST
                    self.res_and_fini(res)
                    return
                device_imei = info["device_imei"]
            if device_imei is None or device_imei == "":
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return

            info = yield device_dao.get_device_info(device_imei,
                                                    ("light_status", ))
            if not info:
                logging.warning("OnGetDeviceSwitchLightStatus, not found, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return

            res["light_status"] = info["light_status"]
        except Exception, e:
            logging.error("OnGetDeviceSwitchLightStatus, error, %s %s",
                          self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

# 成功
        logging.debug("OnGetPetInfo, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()