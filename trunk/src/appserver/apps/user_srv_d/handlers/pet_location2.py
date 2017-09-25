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


class PetLocation2(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("PetLocation2, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
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
            logging.warning("PetLocation2, invalid args, %s, exception %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        # 检查token
        # st = yield self.check_token("PetLocation2", res, uid, token)
        # if not st:
        #    return

        try:
            info = yield pet_dao.get_user_pets(uid, ("pet_id", "device_imei"))
            if info is None or pet_id != info["pet_id"]:
                logging.warning("PetLocation2, not found, %s", self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            res_info = yield pet_dao.get_location_infos(pet_id)

            if res_info is not None:
                length = res_info.count()
                if length > 0:
                    tmp = res_info[length - 1]
                    print tmp
                    res["wifi_data"] = {}
                    res["base_data"] = {}
                    locator_time = int(time.mktime(tmp[
                        "locator_time"].timetuple()))
                    lnglat2 = tmp.get("lnglat2", None)
                    if lnglat2 is not None and len(lnglat2) != 0:
                        radius2 = tmp.get("radius2", -1)
                        location2 = {"longitude": "%.7f" % lnglat2[0],
                                     "latitude": "%.7f" % lnglat2[1],
                                     "radius": radius2,
                                     "location_time": locator_time}
                        res["wifi_data"] = location2

                    lnglat3 = tmp.get("lnglat3", None)
                    if lnglat3 is not None and len(lnglat3) != 0:
                        radius3 = tmp.get("radius3", -1)
                        location3 = {"longitude": "%.7f" % lnglat3[0],
                                     "latitude": "%.7f" % lnglat3[1],
                                     "radius": radius3,
                                     "location_time": locator_time}
                        res["base_data"] = location3

            else:
                res["status"] = error_codes.EC_NODATA
        except Exception, e:
            logging.exception(e)
            logging.warning("PetLocation2, sys_error, %s, exception %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
