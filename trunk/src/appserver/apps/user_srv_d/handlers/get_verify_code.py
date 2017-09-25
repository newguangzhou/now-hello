# -*- coding: utf-8 -*-

import tornado.web
import json
import urllib

import logging
import traceback

from tornado.web import asynchronous
from tornado import gen
from tornado.httpclient import AsyncHTTPClient

from lib import error_codes
from lib import sys_config
from lib.sys_config import SysConfig
from lib import utils
from helper_handler import HelperHandler


class GetVerifyCode(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnGetVerifyCode, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")

        auth_dao = self.settings["auth_dao"]
        conf = self.settings["appconfig"]
        msg_rpc = self.settings["msg_rpc"]

        res = {"status": error_codes.EC_SUCCESS}

        # 获取请求参数
        phone_num = None
        type = None
        try:
            phone_num = self.get_argument("phone_num")
            type = int(self.get_argument("type"))
            if type not in (1, 2):
                self.arg_error("type")
        except Exception, e:
            logging.warning("OnGetVerifyCode, invalid args, %s %s",
                            self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return
        code = 0

        ret = utils.is_valid_phone_num(phone_num)
        if not ret:
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        #
        try:
            # 检查账号是否已经注册
            #uid = yield self.check_account_exist_by_phone_num(
            #    "OnGetVerifyCode", res, phone_num)
            #if not uid:
            #    return

            # 检查账号状态
            #st = yield self.check_account_status("OnGetVerifyCode", res, uid)
            #if not st:
            #    return
            # 生成验证码

            code, ec, extra = yield auth_dao.gen_user_verify_code(
                type, phone_num,
                SysConfig.current().get(sys_config.SC_VERIFY_CODE_LEN),
                SysConfig.current().get(sys_config.SC_VERIFY_CODE_EXPIRE_SECS),
                SysConfig.current().get(sys_config.SC_VERIFY_CODE_FREQ_SECS),
                86400, SysConfig.current().get(
                    sys_config.SC_VERIFY_CODE_FREQ_DAY_COUNT))
            if ec == error_codes.EC_FREQ_LIMIT:
                res["remain_time"] = extra
            if ec != error_codes.EC_SUCCESS:
                logging.warning(
                    "OnGetVerifyCode, gen failed, ec=%u extra=%s %s", ec,
                    str(extra), self.dump_req())
                res["status"] = ec
                self.res_and_fini(res)
                return

            res["code"] = code
            res["next_req_interval"] = SysConfig.current().get(
                sys_config.SC_VERIFY_CODE_FREQ_SECS)
            # 发送短信
        except Exception, e:
            logging.error("OnGetVerifyCode, error, %s %s", self.dump_req(),
                          self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        # 成功
        logging.debug("OnGetVerifyCode, success, code=%s %s", code,
                      self.dump_req())
        self.res_and_fini(res)
        # 发送短信
        try:
            yield msg_rpc.send_verify_code(phone_num, code, "小毛球app")
        except Exception, e:
            logging.warning(
                "OnGetVerifyCode, send sms error, ignore this, code=%s %s %s",
                code, self.dump_req(), self.dump_exp(e))

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
