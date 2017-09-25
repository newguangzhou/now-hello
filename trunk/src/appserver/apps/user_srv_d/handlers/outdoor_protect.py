# -*- coding: utf-8 -*-
from tornado.web import asynchronous
from tornado import gen
import logging
from helper_handler import HelperHandler
from lib import error_codes


#户外保护开关
class OutdoorOnOff(HelperHandler):
    @gen.coroutine
    @asynchronous
    def _deal_request(self):
        logging.debug("OutdoorOnOff, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        res = {"status": error_codes.EC_SUCCESS}
        pet_dao = self.settings["pet_dao"]
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            outdoor_on_off=int(self.get_argument("outdoor_on_off"))
        except Exception,e:
            logging.warning("OutdoorOnOff, invalid args, %s %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return
        st = yield self.check_token("OutdoorOnOff", res, uid, token)
        if not st:
            return
        try:
            set_res = yield pet_dao.set_outdoor_on_off(uid, outdoor_on_off)
            if set_res.matched_count <= 0:
                logging.warning("OutdoorOnOff, set fail, %s", self.dump_req())
                res["status"] = error_codes.EC_SYS_ERROR
                self.res_and_fini(res)
        except Exception, e:
            logging.warning("OutdoorOnOff, error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        logging.debug("OutdoorOnOff, success %s", self.dump_req())
        self.res_and_fini(res)


    def get(self):
        return self._deal_request()
    def post(self):
        return self._deal_request()







#设置户外热点
class SetOutdoorWifi(HelperHandler):
    @gen.coroutine
    @asynchronous
    def _deal_request(self):
        logging.debug("SetOutdoorWifi, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        res = {"status": error_codes.EC_SUCCESS}
        pet_dao = self.settings["pet_dao"]
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            outdoor_wifi_ssid=self.get_argument("wifi_ssid")
            outdoor_wifi_bssid=self.get_argument("wifi_bssid")
            outdoor_wifi={"outdoor_wifi_ssid":outdoor_wifi_ssid,"outdoor_wifi_bssid":outdoor_wifi_bssid}
        except Exception, e:
            logging.warning("SetOutdoorWifi, invalid args, %s %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return
        st = yield self.check_token("SetOutdoorWifi", res, uid, token)
        if not st:
            return
        try:
            set_res=yield pet_dao.set_outdoor_wifi(uid,outdoor_wifi)
            if set_res.matched_count <= 0:
                logging.warning("SetOutdoorWifi, set fail, %s", self.dump_req())
                res["status"] = error_codes.EC_SYS_ERROR
                self.res_and_fini(res)

        except Exception,e:
            logging.warning("SetOutdoorWifi, error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        logging.debug("SetOutdoorWifi, success %s", self.dump_req())
        self.res_and_fini(res)


    def get(self):
        return self._deal_request()

    def post(self):
        return self._deal_request()

