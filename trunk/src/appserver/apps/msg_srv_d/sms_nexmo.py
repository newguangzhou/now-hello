# -*- coding: utf-8 -*-


"""
使用nexmo的短信发送服务
"""


import urllib 
import logging

import traceback
import json
from tornado import ioloop, gen
from tornado.httpclient import AsyncHTTPClient 
import tornado.escape
class NEXMOSMSException(Exception):
    def __init__(self, message):
        self._message = message 
        
    def __str__(self):
        return self._message 

class NEXMOSMS(object):
    def __init__(self, pyloader):
        self._pyloader = pyloader

    @gen.coroutine
    def open(self):
        raise gen.Return(True)

    @gen.coroutine
    def send_sms(self, phone, sms):
        conf = self._pyloader.ReloadInst("Config")
        params = {
            'api_key': conf.nexmo_key,
            'api_secret': conf.nexmo_secret,
            'to': "86%s" % phone,
            'from': '46000',
            'text':  sms
        }
        http_client = AsyncHTTPClient()
        res = yield http_client.fetch(
            "https://rest.nexmo.com/sms/json",
            method = "POST",
            body = urllib.urlencode(params), 
            connect_timeout = 20, 
            request_timeout = 20)

        if res.error:
            logging.error(res.error)
        else:
            #logging.info()
            try:
                json_res = tornado.escape.json_decode(res.body) 
                if json_res["messages"][0]["status"] != "0":
                    raise NEXMOSMSException("Send nexmo sms error phone_num=%s sms=\"%s\" error=%s" % (phone, sms, str(json_res)))
            except Exception, e:
                logging.error("Send nexmo sms error phone_num=%s sms=\"%s\" error=%s", phone, sms, str(e))
                raise e
        logging.info("Send nexmo sms, phone_num=%s sms=\"%s\" res end ", phone, sms)
        raise gen.Return(True)

