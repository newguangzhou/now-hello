# -*- coding: utf-8 -*-

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
from terminal_base import terminal_commands

from lib import sys_config
from lib.sys_config import SysConfig


class AgreePolicy(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("coroutine, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        res = {"status": error_codes.EC_SUCCESS}

        uid = None
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            st = yield self.check_token("AgreePolicy", res, uid, token)
            if not st:
               return
        except Exception, e:
            logging.warning("AgreePolicy, invalid args, %s %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

# 成功
        logging.debug("AgreePolicy, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()