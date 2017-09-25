# -*- coding: utf-8 -*-

import tornado.web
import json
import hashlib
import random
import time

import logging
import traceback

from tornado.web import asynchronous
from tornado import gen

from lib import error_codes
from lib import xmq_web_handler
from lib import type_defines
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor


class PushIOS(xmq_web_handler.XMQWebHandler):
    executor = ThreadPoolExecutor(5)

    @gen.coroutine
    def _deal_request(self):
        logging.debug("PushIOS, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        res = {"status": error_codes.EC_SUCCESS}
        uids = self.get_argument("uids", "")
        if uids == "":
            res["status"] = error_codes.EC_INVALID_ARGS
        else:
            desc = self.get_str_arg("desc")

            payload = self.get_str_arg("payload")
            extra=self.get_str_arg("extra")
            push_type = self.get_argument("push_type", "alias")
            if push_type == "alias":
                yield self.send_to_alias_ios(uids, desc, payload)
            elif push_type == "user_account":
                yield self.send_to_useraccount_ios(uids,payload, {"type":extra})

        self.res_and_fini(res)
        return

    @run_on_executor
    def send_to_useraccount_ios(self, str_uids, payload, extra):
        xiaomi_push2 = self.settings["xiaomi_push2"]
        return xiaomi_push2.send_to_useraccount_ios(str_uids, payload, extra)

    @run_on_executor
    def send_to_alias_ios(self, str_uids, desc, extras):
        xiaomi_push2 = self.settings["xiaomi_push2"]
        return xiaomi_push2.send_to_alias_ios(str_uids,desc,extras)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()

