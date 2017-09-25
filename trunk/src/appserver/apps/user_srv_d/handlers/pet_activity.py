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

class PetActivity(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnPetActivity, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        conf = self.settings["appconfig"]
        
        res = {"status":error_codes.EC_SUCCESS}

        uid = None
        token = None
        pet_id = None
        activity_type = None
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")

            st = yield self.check_token("OnPetActivity", res, uid, token)
            if not st:
                return
            pet_id = int(self.get_argument("pet_id"))
            activity_type = int(self.get_argument("activity_type"))
            if activity_type not in (0,1,2) or pet_id == -1:
                self.arg_error("activity_type")
            else:
                try:
                    yield pet_dao.update_pet_info(pet_id,pet_status=activity_type)
                except Exception, e:
                    logging.warning("OnPetActivity, error, %s %s", self.dump_req(), self.dump_exp(e))
                    res["status"] = error_codes.EC_SYS_ERROR
                    self.res_and_fini(res)
                    return
        except Exception,e:
            logging.warning("OnPetActivity, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return 

   # 成功
        logging.debug("OnPetActivity, success %s",  self.dump_req())
        self.res_and_fini(res)
    
    def post(self):
        return self._deal_request()
    
    def get(self):
        return self._deal_request()