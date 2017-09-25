# -*- coding=utf-8 -*-
import logging
from lib import error_codes
from helper_handler import HelperHandler
class Suggest(HelperHandler):
    def _deal_request(self):
        logging.debug("Suggest, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        res = {"status": error_codes.EC_SUCCESS}

        
        self.res_and_fini(res)
    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()