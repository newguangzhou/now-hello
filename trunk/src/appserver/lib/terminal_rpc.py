# -*- coding: utf-8 -*-

import urllib
import time
import logging
import uuid
import json
import traceback

from tornado import gen
from tornado.httpclient import AsyncHTTPClient

import type_defines
import error_codes


class TerminalRPCException(Exception):
    def __init__(self, message, *args):
        self._message = message % tuple(args)

    def __str__(self):
        return self._message


class TerminalRPC:
    def __init__(self, msg_url):
        self._apis = {"send_j13": "%s/send_commandj13" % (msg_url, ),
                      "send_command_params":
                      "%s/send_command_params" % (msg_url, ), }

    @gen.coroutine
    def call(self, api, **args):
        body = args
        print self._apis[api]
        http_client = AsyncHTTPClient()
        res = yield http_client.fetch(self._apis[api],
                                      method="POST",
                                      body=urllib.urlencode(body),
                                      connect_timeout=10,
                                      request_timeout=10)
        res = json.loads(res.body)
        #if res["status"] != error_codes.EC_SUCCESS:
        #raise TerminalRPCException("Call error, status=%u", res["status"])
        raise gen.Return(res)

    @gen.coroutine
    def send_j13(self, imei):
        ret = yield self.call("send_j13", imei=imei)
        raise gen.Return(ret)

    @gen.coroutine
    def send_command_params(self, **args):
        ret = yield self.call("send_command_params", **args)
        raise gen.Return(ret)
