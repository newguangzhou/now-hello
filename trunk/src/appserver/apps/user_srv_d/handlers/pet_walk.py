# -*- coding: utf-8 -*-

import json
import urllib
import logging
import traceback
from lib import error_codes

from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

class PetWalk(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnPetWalk, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        uid = None
        token = None
        walk_status = None
        pet_id = None
        res = {"status": error_codes.EC_SUCCESS}
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            pet_id = int(self.get_argument("pet_id"))
            walk_status = int(self.get_argument("walk_status"))
        except Exception, e:
            logging.warning("OnPetWalk, invalid args, %s, exception %s", self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

      
        if walk_status not in (1, 2):
            logging.warning("OnPetWalk, invalid args, %s, exception %s", self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        # 检查token
        #st = yield self.check_token("OnOnPetWalk", res, uid, token)
        #if not st:
        #    return

        try:
            info = yield pet_dao.get_user_pets(uid, ("pet_id",))
            if info is None or pet_id != info["pet_id"]:
                logging.warning("OnPetWalk, not found, %s", self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
        except Exception, e:
            logging.warning("OnPetWalk, sys_error, %s, exception %s", self.dump_req(), str(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        #res["longitude"] = "113.3882"
        #res["latitude"] = "22.9432"

        pet_status = 1 if walk_status == 1 else 0

        try:
            yield pet_dao.update_pet_info(pet_id, pet_status=pet_status, pet_no_search_status = pet_status)
        except Exception, e:
            logging.warning("OnPetWalk, error, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
