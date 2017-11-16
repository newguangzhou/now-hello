# -*- coding: utf-8 -*-
import logging
from tornado.web import asynchronous
from tornado import gen

from helper_handler import HelperHandler
from lib import error_codes


class AppConfig(HelperHandler):

    @gen.coroutine
    @asynchronous
    def _deal_request(self):
        logging.debug("AppConfig, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        res = {"status": error_codes.EC_SUCCESS}
        force_update=0
        try:
            version = self.get_argument("version")
            if version < '1.0.5':
                force_update=1
        except Exception,e:
            logging.warning("AppConfig, invalid args, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        res["force_update"]=force_update
        logging.debug("AppConfig, success %s", res["force_update"])
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()