# -*- coding: utf-8 -*-
from tornado.web import asynchronous
from tornado import gen
import logging

from lib import error_codes

from helper_handler import HelperHandler

class DeviceStatus(HelperHandler):
    @gen.coroutine
    @asynchronous
    def _deal_request(self):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        uid = None
        token = None
        imei = None
        res = {"status": error_codes.EC_SUCCESS}
        pet_dao = self.settings["pet_dao"]
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            imei = int(self.get_argument("imei"))
        except Exception, e:
            logging.warning("device_status, invalid args, %s, exception %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return
        # 检查token
        st = yield self.check_token("DeviceStatus", res, uid, token)
        if not st:
            return
        try:
            info =yield pet_dao.get_user_pets(uid,("device_imei","device_status"))
            if imei != info["device_imei"]:
                logging.warning("device_status, not found, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            res["device_status"]=info["device_status"]
        except Exception , e:
            logging.exception(e)
            logging.warning("device_status, sys_error, %s, exception %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return


        # 成功
        logging.debug("OnLogin, success %s", self.dump_req())
        self.res_and_fini(res)

    def get(self):
       return self._deal_request()

    def post(self):
       return self._deal_request()


