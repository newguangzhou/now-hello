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
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from lib import error_codes
from lib import xmq_web_handler


class SendVerify(xmq_web_handler.XMQWebHandler):
    executor = ThreadPoolExecutor(5)

    @run_on_executor
    def send_verify_code(self, code, product, phones):
        sender = self.settings["verify_sender"]
        return sender(code, product, phones)

    @gen.coroutine
    def _deal_request(self):
        logging.debug("SendVerify, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        phone_nums = None
        code = None
        product = None
        res = {"status": error_codes.EC_SUCCESS}
        try:
            phone_nums = self.get_argument("phones")
            code = self.get_argument("code")
            product = self.get_argument("product")
        except Exception, e:
            logging.exception("OnSendSMS, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
        else:
            ok = yield self.send_verify_code(code, product, phone_nums)
            if not ok:
                res = {"status": error_codes.EC_FAIL}
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
