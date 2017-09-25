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



class SetTargetStep(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("SetTargetStep, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        conf = self.settings["appconfig"]
        res = {"status":error_codes.EC_SUCCESS}

        uid = None
        pet_id = -1
        target_step = None
        target_energy = None


        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            st = yield self.check_token("OnSetTargetStep", res, uid, token)
            if not st:
               return
            target_energy = float(self.get_argument("target_energy"))
            pet_id = int(self.get_argument("pet_id", -1))
            target_step = int(self.get_argument("target_step"))
        except Exception, e:
            logging.warning("OnSetTargetStep, invalid args, %s %s", self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        

        try:
            info = yield pet_dao.get_user_pets(uid, ("pet_id",))
            if info is None or (pet_id != -1 and pet_id != info["pet_id"]):
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return          
            yield pet_dao.update_pet_info(info["pet_id"], target_step=target_step, target_energy = target_energy)
        except Exception, e:
            logging.warning("OnSetTargetStep, error, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return


   # 成功
        logging.debug("OnSetTargetStep, success %s",  self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
