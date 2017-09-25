# -*- coding: utf-8 -*-
import json
import urllib
import logging
import traceback
from lib import error_codes
import datetime
import time
from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

from lib import utils
from lib import sys_config
from lib.sys_config import SysConfig


class GetWifiList(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnGetWifiListStatus, %s", self.dump_req())

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
            #device_imei = self.get_argument("imei", None)
        except Exception, e:
            logging.warning("GetWifiList, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        try:
            st = yield self.check_token("OnGetWifiList", res, uid, token)
            if not st:
               return

            info = yield pet_dao.get_user_pets(uid,
                                               ("device_imei", "home_wifi"))
            if not info:
                logging.warning("GetWifiList, not found, %s", self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            device_imei = info.get("device_imei", None)
            home_wifi = info.get("home_wifi", None)
            if device_imei is None or device_imei == "":
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return
            res["data"] = []
            ten_minutes_wifi = yield device_dao.get_ten_minutes_wifi_info(device_imei)
            if ten_minutes_wifi is not None:
                all_wifis = []
                all_wifi_names = []
                for col in ten_minutes_wifi:
                    logging.info("ten_minutes_wifi:%s",col )
                    tmp = utils.change_wifi_info(col["wifi_info"], True)
                    for item in tmp:
                        if item["wifi_bssid"] not in all_wifi_names:
                            last_item = {}
                            last_item["wifi_ssid"] = item["wifi_ssid"]
                            last_item["wifi_bssid"] = item["wifi_bssid"]
                            last_item["wifi_power"] = item["deep"]

                            if home_wifi is not None and home_wifi[
                                    "wifi_ssid"] == last_item[
                                        "wifi_ssid"] and home_wifi[
                                            "wifi_bssid"] == last_item[
                                                "wifi_bssid"]:
                                last_item["is_homewifi"] = 1
                            else:
                                last_item["is_homewifi"] = 0
                            all_wifi_names.append(item["wifi_bssid"])
                            all_wifis.append(last_item)
                logging.info("all_wifis:%s", all_wifis)
                all_wifis.sort(key=lambda obj: int(obj.get('wifi_power')), reverse=True)
                res["data"] = all_wifis
                res["get_wifi_list_time"]=int(time.mktime(datetime.datetime.now().timetuple()))

        except Exception, e:
            logging.error("OnGetWifiListStatus, error, %s %s",
                          self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

# 成功
        logging.debug("OnGetWifiList, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()