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


class RemoveDeviceInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("RemoveDeviceInfo, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        device_dao = self.settings["device_dao"]
        pet_dao = self.settings["pet_dao"]
        conf = self.settings["appconfig"]
        res = {"status": error_codes.EC_SUCCESS}

        uid = None
        token = None
        imei = None
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            st = yield self.check_token("OnAddDeviceInfo", res, uid, token)
            if not st:
               return

            imei = self.get_argument("imei")
        except Exception, e:
            logging.warning("RemoveDeviceInfo, invalid args, %s %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return
        info = yield pet_dao.get_user_pets(uid, ("pet_id", "device_imei"))
        if info is None:
            res["status"] = error_codes.EC_PET_NOT_EXIST
            self.res_and_fini(res)
            return
        device_imei = info.get("device_imei", None)
        if device_imei is None:
            res["status"] = error_codes.EC_DEVICE_NOT_EXIST
            self.res_and_fini(res)
            return

        try:
            yield pet_dao.unbind_device_imei(info["pet_id"])
        except Exception, e:
            logging.warning("RemoveDeviceInfo, pet_dao.unbind_device_imei error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        # try:
        #     yield device_dao.unbind_device_imei(device_imei)
        # except Exception, e:
        #     logging.warning("RemoveDeviceInfo, device_dao.unbind_device_imei error, %s %s", self.dump_req(),
        #                     self.dump_exp(e))
        #     res["status"] = error_codes.EC_SYS_ERROR
        #     self.res_and_fini(res)
        #     return

# 成功
        logging.debug("RemoveDeviceInfo, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
