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


class GetDeviceInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnGetDeviceInfo, %s", self.dump_req())

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
            logging.warning("OnGetDeviceInfo, invalid args, %s",
                            self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        try:
            st = yield self.check_token("OnGetDeviceInfo", res, uid, token)
            if not st:
               return
            if device_imei is None:
                info = yield pet_dao.get_user_pets(uid, ("device_imei", ))
                if not info:
                    logging.warning("OnGetDeviceInfo, not found, %s",
                                    self.dump_req())
                    res["status"] = error_codes.EC_PET_NOT_EXIST
                    self.res_and_fini(res)
                    return
                device_imei = info.get("device_imei", None)
            if device_imei is None or device_imei == "":
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return

            info = yield device_dao.get_device_info(
                device_imei, ("device_name", "iccid", "hardware_version",
                              "software_version", "electric_quantity", "sim_deadline","j01_repoter_date",
                              "battery_status"))
            if not info:
                logging.warning("OnGetDeviceInfo, not found, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return

            res["firmware_version"] = info.get("software_version", "")
            res["hardware_version"] = info.get("hardware_version", "")
            battery_last_get_time = info.get("j01_repoter_date","")
            if battery_last_get_time != "":
                battery_last_get_time = utils.date2str(battery_last_get_time)

            res["battery_last_get_time"] = battery_last_get_time
            sim_deadline = info.get("sim_deadline", "")
            if sim_deadline != "":
                sim_deadline = utils.date2str(sim_deadline)
            res["battery_level"] = info.get("electric_quantity", -1)
            res["sim_deadline"] = sim_deadline
            res["imei"] = device_imei
            res["battery_status"]=info.get("battery_status",0)
        except Exception, e:
            logging.error("OnGetPetInfo, error, %s %s", self.dump_req(),
                          self.dump_exp(e))
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