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


class SendGetWifiListCmd(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("coroutine, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        terminal_rpc = self.settings["terminal_rpc"]
        conf = self.settings["appconfig"]
        res = {"status": error_codes.EC_SUCCESS}

        uid = None
        pet_id = -1
        target_step = None

        try:
            uid = int(self.get_argument("uid"))
            pet_id = int(self.get_argument("pet_id", -1))
            token = self.get_argument("token")
            st = yield self.check_token("OnSetTargetStep", res, uid, token)
            if not st:
               return

            if pet_id > 0:
                info = yield pet_dao.get_pet_info_by_petid(pet_id ,("device_imei",))
            else:
                info = yield pet_dao.get_user_pets(uid, ("pet_id", "device_imei"))
            if info is None:
                logging.warning("SendGetWifiListCmd, uid:%d, pet_id:%d not found, %s",
                                uid, pet_id, self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            imei = info.get("device_imei", None)
            if imei is None:
                logging.warning("SendGetWifiListCmd, not found, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return
            get_res = yield terminal_rpc.send_j13(imei)
            res["status"] = get_res["status"]

        except Exception, e:
            logging.warning("SendGetWifiListCmd, invalid args, %s %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

# 成功
        logging.debug("SendGetWifiListCmd, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
