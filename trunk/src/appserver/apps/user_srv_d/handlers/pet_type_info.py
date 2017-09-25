# -*- coding: utf-8 -*-

import json
import urllib
import logging
import traceback
from lib import error_codes

from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler


class PetTypeInfo(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnPetTypeInfo, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        res = {"status": error_codes.EC_SUCCESS, "data": [
            {"pet_type_name": "秋田犬", "pet_type_id": 1, "img_url": "http://www.daliulian.net/imgs/image/14/1495849.jpg"},
            {"pet_type_name": "shabi犬", "pet_type_id": 2, "img_url": "http://petbird.tw/wp-content/uploads/2013/07/yyoo9.jpg"}]}
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
