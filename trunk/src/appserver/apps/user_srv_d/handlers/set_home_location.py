# -*- coding: utf-8 -*-
import logging
from lib import error_codes

from tornado import gen
from helper_handler import HelperHandler

# --
# home 位置
# --
# /user/set_home_location
# 方法: POST/GET
# 参数: uid
# token
# longitude 经度
# latitude 纬度
# 返回: {
# status:状态，可能的只有:
# EC_SUCCESS
# EC_INVALID_TOKEN
# EC_INVALID_ARGS
# EC_SYS_ERROR
# EC_UNKNOWN_ERROR
# EC_PET_NOT_EXIST
# EC_DEVICE_NOT_EXIST
# EC_NODATA
# }


class SetHomeLocation(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("SetHomeLocation, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        res = {"status": error_codes.EC_SUCCESS}
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            st = yield self.check_token("SetHomeLocation", res, uid, token)
            if not st:
               return
            longitude = self.get_argument("longitude")
            latitude = self.get_argument("latitude")
        except Exception, e:
            logging.warning("SetHomeLocation, invalid args, %s %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        try:
            set_res = yield pet_dao.set_home_location(uid, {"longitude": longitude,
                                                        "latitude":
                                                            latitude})
            if set_res.matched_count <= 0:
                logging.warning("SetHomeLocation, set fail, %s", self.dump_req())
                res["status"] = error_codes.EC_SYS_ERROR
                self.res_and_fini(res)
                return
        except Exception, e:
            logging.warning("SetHomeLocation, error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

# 成功
        logging.debug("SetHomeLocation, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
