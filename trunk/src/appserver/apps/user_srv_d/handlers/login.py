# -*- coding: utf-8 -*-

import tornado.web
import json
import hashlib
import time

import logging
import traceback

from tornado.web import asynchronous
from tornado import gen

from lib import error_codes
from lib import sys_config
from lib.sys_config import SysConfig
from lib import utils
from helper_handler import HelperHandler

COMMON_PASSWD = "123456"


class Login(HelperHandler):
    @gen.coroutine
    @asynchronous
    def _deal_request(self):
        logging.debug("OnLogin, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")

        res = {"status": error_codes.EC_SUCCESS}
        auth_dao = self.settings["auth_dao"]
        pet_dao=self.settings["pet_dao"]
        custom_headers = self.custom_headers()
        conf = self.settings["appconfig"]

        # 获取请求参数
        phone_num = ""
        device_type = ""
        device_token = ""
        code = ""
        try:
            phone_num = self.get_argument("phone_num")
            device_type = int(self.get_argument("device_type"))
            if device_type != 1 and device_type != 2:
                self.arg_error("device_type")
            device_token = self.get_argument("device_token")
            code = self.get_argument("code")
            x_os_int=custom_headers.get("x_os_int",23)
        except Exception, e:
            logging.warning("OnLogin, invalid args, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        #
        try:

            #验证码则验证
            if phone_num == "13812345678" and code == "000000":
                logging.warn("apple review login ")
            elif phone_num in conf["phone_num_for_test"]:
                logging.warn("we login ")
            else:
                st = yield self.check_verify_code("OnLogin", res, 1, phone_num,
                                                  code)
                if not st:
                    return

            # 检查账号是否已经注册
            uid = yield auth_dao.has_user_auth_info_by_mobile_num(phone_num)
            logging.info(uid)
            if uid is None:
                #注册
                uid = yield self.register(phone_num, x_os_int)
                try:
                    pet_id = int(time.time() * -1000)
                    device_imei = int(time.time() * -1000)
                    yield pet_dao.update_pet_info_by_uid(uid,pet_id=pet_id,device_imei=device_imei,mobile_num=phone_num)
                except Exception, ex:
                    logging.error("update pet info by uid error %s", ex)
            else:
                # 检查账号状态
                st = yield self.check_account_status("OnLogin", res, uid)
                if not st:
                    return

        # 生成token
            expire_secs = SysConfig.current().get(
                sys_config.SC_TOKEN_EXPIRE_SECS)
            token = yield auth_dao.gen_user_token(uid, True, device_type,device_token,
                expire_secs, custom_headers["platform"], custom_headers["device_model"],x_os_int)
            res["uid"] = uid
            res["token"] = token
            res["token_expire_secs"] = expire_secs

        except Exception, e:
            logging.error("OnLogin, error, %s %s", self.dump_req(),
                          self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        # 成功
        logging.debug("OnLogin, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()

    @gen.coroutine
    def register(self, phone_num, client_os_ver):
        auth_dao = self.settings["auth_dao"]
        user_dao = self.settings["user_dao"]
        gid_rpc = self.settings["gid_rpc"]
        uid = yield gid_rpc.alloc_user_gid()
        yield auth_dao.add_user_auth_info(phone_num, uid, COMMON_PASSWD)

        # 添加用户信息
        try:
            yield user_dao.add_user_info(uid=uid, phone_num=phone_num, client_os_ver = client_os_ver)
        except Exception, e:
            utils.recover_log("user login error", uid=uid, phone_num=phone_num, client_os_ver = client_os_ver)
            raise e
        raise gen.Return(uid)
