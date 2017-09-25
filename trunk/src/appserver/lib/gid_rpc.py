# -*- coding: utf-8 -*-

import urllib
import time
import logging
import sys
import uuid
import json
import traceback
from zlib import crc32
from tornado import gen
from tornado.httpclient import AsyncHTTPClient

import type_defines
import error_codes


class GIDRPCException(Exception):
    def __init__(self, message, *args):
        self._message = message % tuple(args)

    def __str__(self):
        return self._message


class GIDRPC:
    def __init__(self, url):
        self._url = url

    @gen.coroutine
    def alloc_gid(self, type):
        #params = {"type":type}
        #http_client = AsyncHTTPClient()
        #res = yield http_client.fetch(
        #    self._url,
        #    method = "POST",
        #    body = urllib.urlencode(params),
        #    connect_timeout = 10,
        #    request_timeout = 10)
        #res = json.loads(res.body)
        #if res["status"] != error_codes.EC_SUCCESS:
        #    raise GIDRPCException("Alloc gid error, status=%u", res["status"])
        ret = crc32(str(time.time())) & 0xffffffff
        raise gen.Return(ret)

        # raise gen.Return(int(time.time()))

    @gen.coroutine
    def alloc_user_gid(self):
        ret = yield self.alloc_gid(type_defines.USER_GID)
        raise gen.Return(ret)

    @gen.coroutine
    def alloc_audit_gid(self):
        ret = yield self.alloc_gid(type_defines.AUDIT_GID)
        raise gen.Return(ret)

    @gen.coroutine
    def alloc_pet_gid(self):
        ret = yield self.alloc_gid(type_defines.PET_GID)
        raise gen.Return(ret)
