# -*- coding: utf-8 -*-

import tornado.web
import json
import urllib

import logging
import traceback

from tornado.web import asynchronous
from tornado import gen

from lib import error_codes
from lib import xmq_web_handler
from lib import utils


class HelperHandler(xmq_web_handler.XMQWebHandler):
    @gen.coroutine
    @asynchronous
    def check_account_exist(self, logprefix, res, uid):
        auth_dao = self.settings["auth_dao"]

        # 检查账号是否已经存在
        phone_num = yield auth_dao.has_user_auth_info_by_auth_id(uid)
        if phone_num is None:
            logging.warning("%s, user not exist!, %s", logprefix,
                            self.dump_req())
            res["status"] = error_codes.EC_USER_NOT_EXIST
            self.res_and_fini(res)
            raise gen.Return(None)

        raise gen.Return(phone_num)

    @gen.coroutine
    @asynchronous
    def check_account_exist_by_phone_num(self, phone_num):
        auth_dao = self.settings["auth_dao"]
        # 检查账号是否已经存在
        return auth_dao.has_user_auth_info_by_mobile_num(phone_num)

    @gen.coroutine
    @asynchronous
    def check_verify_code(self, logprefix, res, type, phone_num, code):
        auth_dao = self.settings["auth_dao"]
        ec = yield auth_dao.check_user_verify_code(type, phone_num, code)
        if ec != error_codes.EC_SUCCESS:
            logging.warning("%s, check verify code failed, ec=%u %s",
                            logprefix, ec, self.dump_req())
            res["status"] = ec
            self.res_and_fini(res)
            raise gen.Return(False)
        raise gen.Return(True)

    @gen.coroutine
    @asynchronous
    def check_account_status(self, logprefix, res, uid):
        auth_dao = self.settings["auth_dao"]

        # 检查账号状态
        ec, extra = yield auth_dao.check_user_auth_status(uid)
        if ec != error_codes.EC_SUCCESS:
            logging.warning("%s, check account status failed, ec=%u extra=%s",
                            logprefix, ec, str(extra))
            res["status"] = ec
            if ec == error_codes.EC_ACCOUNT_FREEZED_TEMP:
                res["unfreeze_remain_secs"] = extra
            self.res_and_fini(res)
            raise gen.Return(False)

        raise gen.Return(True)

    @gen.coroutine
    @asynchronous
    def check_token(self, logprefix, res, uid, token):
        auth_dao = self.settings["auth_dao"]
        ec, info = yield auth_dao.check_user_token(uid, token)
        if ec != error_codes.EC_SUCCESS:
            logging.warning("%s, check token failed, ec=%u %s info=%s", logprefix, ec,
                            self.dump_req(), str(info))
            res["status"] = ec
            if ec == error_codes.EC_LOGIN_IN_OTHER_PHONE:
                res["device_model"] = info["device_model"]
                res["msg"] = "您的账号已经在另一台手机登陆"
                res["date"] = utils.date2str(info["mod_date"])
            self.res_and_fini(res)
            raise gen.Return(False)
        raise gen.Return(True)
