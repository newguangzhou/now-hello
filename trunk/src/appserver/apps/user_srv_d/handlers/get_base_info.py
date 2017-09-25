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


class GetBaseInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("GetBaseInfo, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        device_dao = self.settings["device_dao"]
        conf = self.settings["appconfig"]

        res = {"status": error_codes.EC_SUCCESS}

        uid = None
        token = None
        pet_id = -1

        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            pet_id = int(self.get_argument("pet_id", -1))
        except Exception, e:
            logging.warning("GetBaseInfo, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        try:
            st = yield self.check_token("OnGetBaseInfo", res, uid, token)
            if not st:
               return
            res["pet_id"] = 0
            res["device_imei"] = ""
            res["wifi_bssid"] = ""
            res["wifi_ssid"] = ""
            res["has_reboot"] = 0
            res["longitude"]=-1
            res["latitude"]=-1
            res["agree_policy"]=0
            info = yield pet_dao.get_user_pets(uid, ("pet_id", "device_imei",
                                                     "home_wifi","has_reboot","home_location","agree_policy"))
            if not info:
                logging.warning("GetBaseInfo in pet dao, not found, %s", self.dump_req())
                # device_info = yield device_dao.get_device_info_by_uid(uid,("imei",))
                # if not device_info:
                #     logging.warning("GetBaseInfo in device dao, not found, %s", self.dump_req())
                # else:
                #     device_imei = device_info.get("imei", "")
                #     if device_imei is not None:
                #         res["device_imei"] = device_imei
            else:
                pet_id = info.get("pet_id", 0)
                if pet_id < 0:
                    res["pet_id"] = 0
                else:
                    res["pet_id"] = pet_id
                res["has_reboot"] = info.get("has_reboot",0)
                device_imei = info.get("device_imei", "")
                if device_imei is not None and utils.is_imei_valide(str(device_imei)):
                    res["device_imei"] = device_imei
                home_wifi = info.get("home_wifi", None)
                if home_wifi is not None:
                    res["wifi_bssid"] = home_wifi["wifi_bssid"]
                    res["wifi_ssid"] = home_wifi["wifi_ssid"]
                home_location=info.get("home_location",None)
                if home_location is not None:
                    res["longitude"]=home_location["longitude"]
                    res["latitude"]=home_location["latitude"]
                res["agree_policy"]=info.get("agree_policy",0)

        except Exception, e:
            logging.error("GetBaseInfo, error, %s %s", self.dump_req(),
                          self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

# 成功
        logging.debug("GetBaseInfo, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()