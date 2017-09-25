# -*- coding: utf-8 -*-


"""
小米的push推送
"""

import urllib 
import json
import time
import logging
import sys
import uuid
import traceback

from tornado import ioloop, gen
from tornado.httpclient import AsyncHTTPClient

class MIPushException(Exception):
    def __init__(self, msg, *args):
        self._msg = msg % tuple(args)
    
    def __str__(self):
        return self._msg
    
class MIPush:
    def __init__(self, host, appsecret, app_pkg_name):
        self._appsecret = appsecret
        self._app_pkg_name = app_pkg_name
        
        self._apis = {
            "push":"https://%s/v2/message/user_account" % (host,),
            "push_all":"https://%s/v2/message/all" % (host,)
            }
        
    
    @gen.coroutine
    def call(self, api, **args):
        if not self._apis.has_key(api):
            raise MIPushException("MIPush api \"%s\" not exists", api)
        
        body = args 
        headers = {"Authorization":"key=%s" % (self._appsecret,)}
        http_client = AsyncHTTPClient()
        res = yield http_client.fetch(
            self._apis[api],
            method="POST", 
            body = urllib.urlencode(body),
            headers = headers,
            connect_timeout = 10,
            request_timeout = 10)
        
        jres = json.loads(res.body)
        
        logging.debug("Call mipush api, api=\"%s\" res=\"%s\"", self._apis[api], str(jres))
        
        raise gen.Return(jres)
    
    def build_android_noti_msg(self, title, desc, pass_through = 1, noti_id = None, data = ""):
        ret = {
               "payload":data,
               "restricted_package_name":self._app_pkg_name,
               "pass_through":pass_through,
               "notify_type":-1,
               "extra.notify_foreground":0,
               "title":title,
               "description":desc,
        }
        if noti_id:
            ret["notify_id"] = noti_id
        return ret 
    
    def build_ios_noti_msg(self, desc):
        ret = {
               "description":desc
               }
        return ret
    
    @gen.coroutine
    def push_android(self, account, msg):
        msg["user_account"] = str(account)
        
        res = yield self.call("push", **msg)
        if res["code"] != 0:
            raise MIPushException("Push failed, alias=\"%s\", errcode=%d errdesc=\"%s\"", alias, res["code"], res["description"])
        
    @gen.coroutine
    def push_all(self, msg):
        res = yield self.call("push_all", **msg)
        if res["code"] != 0:
            raise MIPushException("Push all failed, errcode=%d errdesc=\"%s\"", res["code"], res["description"])
    
        
    
    