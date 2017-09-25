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


class PushAndrod(xmq_web_handler.XMQWebHandler):
    executor = ThreadPoolExecutor(5)

    @gen.coroutine
    def _deal_request(self):
        logging.debug("PushAndrod, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        res = {"status": error_codes.EC_SUCCESS}
        uids = self.get_argument("uids", "")
        if uids == "":
            res["status"] = error_codes.EC_INVALID_ARGS
        else:
            title = self.get_str_arg("title")
            desc = self.get_str_arg("desc")
            payload = self.get_str_arg("payload")
            pass_through = int(self.get_argument("pass_through", 0))
            push_type = self.get_argument("push_type","alias")
            if push_type == "alias":
                yield self.send_to_alias_android(uids, title, desc, payload,
                                             pass_through)
            elif push_type == "user_account":
                yield self.send_to_useraccount_android(uids, title, desc, payload,
                                                 pass_through)
        self.res_and_fini(res)
        return

    @run_on_executor
    def send_to_useraccount_android(self, str_uids, title, desc, payload,
                              pass_through):
        xiaomi_push2 = self.settings["xiaomi_push2"]
        return xiaomi_push2.send_to_useraccount_android(str_uids, title, desc,
                                                  payload, pass_through)

    @run_on_executor
    def send_to_alias_android(self, str_uids, title, desc, payload,
                              pass_through):
        xiaomi_push2 = self.settings["xiaomi_push2"]
        return xiaomi_push2.send_to_alias_android(str_uids, title, desc,
                                                  payload, pass_through)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()


class Push(xmq_web_handler.XMQWebHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnPush, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")

        res = {"status": error_codes.EC_SUCCESS}
        conf = self.settings["appconfig"]
        auth_dao = self.settings["auth_dao"]
        xiaomi_push = self.settings["xiaomi_push"]

        # 获取请求参数
        uid = None
        title = None
        desc = None
        data = ""
        try:
            uid = int(self.get_argument("uid"))

            if self.request.arguments.has_key("title"):
                title = self.get_str_arg("title")
            else:
                title = conf.default_push_title

            if self.request.arguments.has_key("data"):
                data = self.get_str_arg("data")

            desc = self.get_str_arg("desc")
        except Exception, e:
            logging.warning("OnPush, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

            #
        try:
            devinfo = yield auth_dao.get_device_info(type_defines.USER_AUTH,
                                                     uid)
            if not devinfo:
                logging.warning("OnPush, can not get user device info, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_UNKNOWN_ERROR
                self.res_and_fini(res)
                return

            msg = None
            if devinfo["device_type"] == type_defines.DEVICE_ANDROID:
                msg = xiaomi_push.build_android_noti_msg(title, desc, 1, None,
                                                         data)
                yield xiaomi_push.push_android(uid, msg)
            else:
                pass

        except Exception, e:
            logging.warning("OnPush, failed, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        # 发送成功
        logging.debug("OnPush, success, %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
