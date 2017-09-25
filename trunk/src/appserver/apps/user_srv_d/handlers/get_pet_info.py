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


class GetPetInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("GetPetInfo, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
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
            logging.warning("OnGetPetInfo, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        try:
            st = yield self.check_token("OnGetPetInfo", res, uid, token)
            if not st:
               return

            info = yield pet_dao.get_user_pets(uid, (
                "pet_id", "nick", "logo_url", "birthday", "sex", "device_imei",
                "target_step", "weight", "pet_type_id", "description", "target_energy","recommend_energy"))
            if not info:
                logging.warning("OnGetPetInfo, not found, %s", self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            res["device_imei"] = ""
            for (k, v) in info.items():
                if k == "birthday":
                    res[k] = utils.date2str(v, True)
                elif k == "weight":
                    res[k] = "%.2f" % v
                elif k== "target_energy":
                    res[k] = "%.2f" % v
                elif k=="recommend_energy":
                    res[k]="%.2f" % v
                else:
                    res[k] = v

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