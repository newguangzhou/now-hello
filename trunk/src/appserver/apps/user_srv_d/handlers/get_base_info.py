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

@gen.coroutine
def get_base_info(pet_dao,uid, pet_id):
    logging.debug("get_base_info, uid:%d pet_id:%d", uid, pet_id)
    res = {"status": error_codes.EC_SUCCESS}

    try:
        
        res["pet_id"] = 0
        res["device_imei"] = ""
        res["wifi_bssid"] = ""
        res["wifi_ssid"] = ""
        res["has_reboot"] = 0
        res["longitude"]=-1
        res["latitude"]=-1
        res["agree_policy"]=1
        res["outdoor_on_off"]=0
        res["outdoor_wifi_bssid"]=""
        res["outdoor_wifi_ssid"]=""
        res["outdoor_in_protected"]=0
        if pet_id > 0:
            info = yield pet_dao.get_pet_info_by_petid(pet_id, ( "device_imei",
                                                                 "home_wifi","has_reboot","home_location","agree_policy","outdoor_on_off","outdoor_wifi","outdoor_in_protected"))
        else:
            info = yield pet_dao.get_user_pets(uid, ("pet_id", "device_imei",
                                                     "home_wifi","has_reboot","home_location","agree_policy","outdoor_on_off","outdoor_wifi","outdoor_in_protected"))
            if info:
                pet_id = info.get("pet_id", 0)
        if not info or pet_id <= 0:
            logging.warning("GetBaseInfo in pet dao, not found,uid:%d pet_id:%d",
                            uid, pet_id)
            #res["status"] = error_codes.EC_PET_NOT_EXIST
            #raise gen.Return(res)
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
            res["outdoor_on_off"]=int(info.get("outdoor_on_off",0))
            outdoor_wifi=info.get("outdoor_wifi",None)
            if outdoor_wifi is not None:
                res["outdoor_wifi_bssid"] = outdoor_wifi["outdoor_wifi_bssid"]
                res["outdoor_wifi_ssid"]=outdoor_wifi["outdoor_wifi_ssid"]
            res["outdoor_in_protected"]=info.get("outdoor_in_protected",0)
            res["pet_count"] = yield pet_dao.get_pet_count(uid)

    except Exception, e:
        logging.error("get_base_info fail ,err:%s trace:%s",str(e), traceback.format_exc())
        res["status"] = error_codes.EC_SYS_ERROR
    raise gen.Return( res)

class GetBaseInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("GetBaseInfo, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        custom_headers = self.custom_headers()
        res = {"status": error_codes.EC_SUCCESS}
        x_os_int = 23
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            pet_id = int(self.get_argument("pet_id", -1))
            try:
                x_os_int = int(custom_headers.get("x_os_int", 23))
            except Exception, e:
                pass
        except Exception, e:
            logging.warning("GetBaseInfo, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return
        st = yield self.check_token("OnGetBaseInfo", res, uid, token)
        pet_dao = self.settings["pet_dao"]
        user_dao = self.settings["user_dao"]
        if not st:
            res["status"] = error_codes.EC_USER_NOT_LOGINED
        else:
            res = yield get_base_info(pet_dao, uid, pet_id)
        if res["status"] == error_codes.EC_SUCCESS:
            yield user_dao.update_user_info(uid,client_os_ver =x_os_int,choice_petid = res["pet_id"])
            logging.debug("GetBaseInfo, success req:%s res:%s", self.dump_req(),res)
        else:
            logging.error("GetBaseInfo, error, req:%s res:%s", self.dump_req(),res)
        self.res_and_fini(res)
    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
