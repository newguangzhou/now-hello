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


class GetPetStatusInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("GetPetStatusInfo, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        device_dao=self.settings["device_dao"]
        conf = self.settings["appconfig"]

        res = {"status": error_codes.EC_SUCCESS}

        uid = None
        token = None
        pet_id = -1
        device_imei=None

        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            pet_id = int(self.get_argument("pet_id", -1))
        except Exception, e:
            logging.warning("GetPetStatusInfo, invalid args, %s",
                            self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        try:
            st = yield self.check_token("OnGetPetStatusInfo", res, uid, token)
            if not st:
                return
            cols = ("pet_id","pet_status","pet_is_in_home","device_status","device_imei",
                    "outdoor_in_protected","outdoor_on_off")
            if pet_id < 0:
                info = yield pet_dao.get_user_pets(uid, cols)
                if info is not None:
                    pet_id = info.get("pet_id",-1)
            else:
                info = yield pet_dao.get_pet_info_by_petid(pet_id, cols)
            if not info:
                logging.warning("GetPetStatusInfo,uid:%d pet_id:%d not found, %s",
                                uid, pet_id, self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            device_imei=info["device_imei"]
            res["pet_status"] = info.get("pet_status",0)
            res["pet_is_in_home"]=info.get("pet_is_in_home",1)
            # res["device_status"]=info.get("device_status",1)
            res["device_status"] = 1
            res["outdoor_in_protected"]=info.get("outdoor_in_protected",0)
            res["outdoor_on_off"]=info.get("outdoor_on_off",0)

        except Exception, e:
            logging.error("GetPetStatusInfo, error, %s %s", self.dump_req(),
                          self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        try:
            info = yield device_dao.get_device_info(
                device_imei, ("electric_quantity","app_electric_quantity","j01_repoter_date","battery_status"))
            if not info:
                logging.warning("GetPetStatusInfo, not found, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return
            battery_last_get_time = info.get("j01_repoter_date", "")
            if battery_last_get_time != "":
                battery_last_get_time = utils.date2str(battery_last_get_time)
            res["battery_last_get_time"] = battery_last_get_time
            electric_quantity=info.get("electric_quantity",-1)
            res["battery_level"] = info.get("app_electric_quantity", electric_quantity)
            res["battery_status"]=info.get("battery_status",0)

            #增加状态提示
            location_info = yield pet_dao.get_last_location_info(pet_id)
            if location_info is not None:
                res["locator_status"] = location_info["locator_status"]
                res["station_status"] = location_info.get("station_status", 0)
                if res["device_status"]  == 0:

                    if electric_quantity == 0:
                        res["offline_reason"] = 1 #电量为零
                    elif res["station_status"] == 1:
                        res["offline_reason"] = 2   #移动网络信号差
                    else:
                        res["offline_reason"] = 3   #其他

        except Exception,e:
            logging.debug("GetPetStatusInfo, req:%s error:%s", self.dump_req(),e.message)
            self.res_and_fini(res)
            return

# 成功
        logging.debug("GetPetStatusInfo, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
