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
from helper_handler import HelperHandler
from lib import utils


class Register(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnRegister, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")

        res = {"status": error_codes.EC_SUCCESS}
        auth_dao = self.settings["auth_dao"]
        user_dao = self.settings["user_dao"]
        global_dao = self.settings["global_dao"]
        gid_rpc = self.settings["gid_rpc"]
        conf = self.settings["appconfig"]

        # 获取请求参数
        phone_num = ""
        code = ""
        passwd = ""
        try:
            phone_num = self.get_argument("phone_num").encode("utf8")
            code = self.get_argument("code")
            passwd = self.get_argument("passwd")
        except Exception, e:
            logging.warning("OnRegister, invalid args, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        #
        try:
            # 检查是否已经注册
            uid = yield auth_dao.has_user_auth_info_by_mobile_num(phone_num)
            if uid:
                logging.warning("OnRegister, already registered!, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_USER_ALREADY_REGISTERED
                self.res_and_fini(res)
                return
            # 设置验证信息
            uid = yield gid_rpc.alloc_user_gid()
            yield auth_dao.add_user_auth_info(phone_num, uid, passwd)

            # 添加用户信息
            try:
                yield user_dao.add_user_info(uid=uid, phone_num=phone_num)
            except Exception, e:
                utils.recover_log("user register error",
                                  uid=uid,
                                  phone_num=phone_num)
                raise e
        except Exception, e:
            logging.warning("OnRegister, error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        # 注册成功
        logging.debug("OnRegister, success, %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
