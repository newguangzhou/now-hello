# -*- coding: utf-8 -*-

import json
import urllib
import logging
import traceback
from lib import error_codes
import time
from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler


class PetLocation(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):

        logging.debug("OnPetLocation, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        terminal_rpc = self.settings["terminal_rpc"]
        pet_dao = self.settings["pet_dao"]
        uid = None
        token = None
        res = {"status": error_codes.EC_SUCCESS}
        pet_id = None
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            pet_id = int(self.get_argument("pet_id"))
        except Exception, e:
            logging.warning("OnPetLocation, invalid args, %s, exception %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        # 检查token
        st = yield self.check_token("OnPetLocation", res, uid, token)
        if not st:
            return

        try:
            info = yield pet_dao.get_user_pets(uid, ("pet_id", "device_imei","pet_status"))
            if info is None or pet_id != info["pet_id"]:
                logging.warning("OnPetLocation, not found, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            imei = info["device_imei"]
            if imei is None:
                logging.warning("OnPetLocation, not found, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            else:
                if info.get("pet_status",0) != 2:
                    terminal_rpc.send_j13(imei)

            res_info = yield pet_dao.get_location_infos(pet_id)
            if res_info is not None:
                length = res_info.count()
                if length > 0:
                    tmp = res_info[length - 1]
                    res["longitude"] = "%.7f" % tmp["lnglat"][0]
                    res["latitude"] = "%.7f" % tmp["lnglat"][1]
                    res["radius"] = tmp.get("radius", -1)
                    res["location_time"] = int(time.mktime(tmp[
                        "locator_time"].timetuple()))
                    res["locator_status"]=tmp.get("locator_status",5)
            else:
                res["status"] = error_codes.EC_NODATA
        except Exception, e:
            logging.exception(e)
            logging.warning("OnPetLocation, sys_error, %s, exception %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
