# -*- coding: utf-8 -*-


"""
使用亿美软通的短信发送服务
"""

import urllib 
from xml.dom import minidom
import time
import logging
import sys
import uuid
import traceback

from tornado import ioloop, gen
from tornado.httpclient import AsyncHTTPClient 

class YMRTSMSException(Exception):
    def __init__(self, message):
        self._message = message 
        
    def __str__(self):
        return self._message 
    
class YMRTSMS:
    def __init__(self, pyloader):
        self._pyloader = pyloader
    
    def _parse_common_res(self, res):
        dom = minidom.parseString(res.strip())
        nodes = dom.getElementsByTagName("error")
        error = int(nodes[0].firstChild.nodeValue)
        nodes = dom.getElementsByTagName("message")
        message = ""
        if nodes[0].firstChild:
            message = nodes[0].firstChild.nodeValue
        return (error, message)
    
    @gen.coroutine
    def open(self):
        conf = self._pyloader.ReloadInst("Config")
        
        body = {
                "cdkey":conf.ymrt_cdkey,
                "password":conf.ymrt_passwd
        }
        
        http_client = AsyncHTTPClient()
        res = yield http_client.fetch(
            "http://sdk4report.eucp.b2m.cn:8080/sdkproxy/regist.action",
            method="POST", 
            body = urllib.urlencode(body),
            connect_timeout = 10,
            request_timeout = 10)
            
        error, message = self._parse_common_res(res.body)
        logging.info("Open ymrt sms service, error=%d message=\"%s\"", error, message)
        
        if error != 0: 
            raise YMRTSMSException("Open ymrt sms service failed, error=%d message=\"%s\"" % (error, message))
        
        raise gen.Return(True)
    
    @gen.coroutine
    def send_sms(self, phone, sms):
        conf = self._pyloader.ReloadInst("Config")
        
        body = {
                "cdkey":conf.ymrt_cdkey,
                "password":conf.ymrt_passwd,
                "phone":phone, 
                "message":sms,
                "seqid":str(uuid.uuid1()),
                "addserial":""
            }
        
        http_client = AsyncHTTPClient()
        res = yield http_client.fetch(
            "http://sdk4report.eucp.b2m.cn:8080/sdkproxy/sendsms.action",
            method = "POST",
            body = urllib.urlencode(body), 
            connect_timeout = 10, 
            request_timeout = 10
            )
            
        error, message = self._parse_common_res(res.body)
        logging.info("Send ymrt sms, phone_num=%s sms=\"%s\" error=%d message=\"%s\"", 
            phone, sms, error, message)
        if error != 0:
            raise YMRTSMSException("Send ymrt sms failed, error=%d message=\"%s\"" % (error, message))
        
        raise gen.Return(True)
