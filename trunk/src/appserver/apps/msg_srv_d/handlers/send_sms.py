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

class SendSMS(xmq_web_handler.XMQWebHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnSendSMS, %s", self.dump_req())
        
        self.set_header("Content-Type", "application/json; charset=utf-8")
        
        res = {"status":error_codes.EC_SUCCESS}
        sms_sender = self.settings["sms_sender"]
        
        # 获取请求参数
        phone_num = None 
        sms = None
        try:
            phone_num = self.get_argument("phone_num")
            sms_type=self.get_argument("sms_type")
            sms = self.get_argument("sms")
            sms = self.decode_argument(sms)
        except Exception,e:
            logging.warning("OnSendSMS, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return
        else:
            ok = yield sms_sender(sms_type,sms,phone_num)
            if not ok:
                res = {"status": error_codes.EC_FAIL}
        # 发送成功
        logging.debug("OnSendSMS, success, %s", self.dump_req())
        self.res_and_fini(res)
        
    def post(self):
        return self._deal_request()
    
    def get(self):
        return self._deal_request()
    
    