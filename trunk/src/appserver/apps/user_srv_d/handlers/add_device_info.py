# -*- coding: utf-8 -*-
import json
import urllib
import logging
import datetime
import traceback
from lib import error_codes
import time
import pymongo
from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

from lib import utils
from lib import sys_config
from lib.sys_config import SysConfig


class AddDeviceInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("AddDeviceInfo, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        device_dao = self.settings["device_dao"]
        pet_dao = self.settings["pet_dao"]
        conf = self.settings["appconfig"]
        terminal_rpc = self.settings["terminal_rpc"]
        gid_rpc = self.settings["gid_rpc"]
        res = {"status": error_codes.EC_SUCCESS}
        custom_headers = self.custom_headers()


        uid = None
        token = None
        imei = None
        device_name = None
        x_os_int=23
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            st = yield self.check_token("OnAddDeviceInfo", res, uid, token)
            if not st:
               return

            imei = self.get_argument("imei")
            device_name = self.get_argument("device_name")
            try:
                x_os_int=custom_headers.get("x_os_int",23)
            except Exception,e:
                pass
        except Exception, e:
            logging.warning("AddDeviceInfo, invalid args, %s %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        if not utils.is_imei_valide(imei) :
            logging.warning("AddDeviceInfo, invalid imei")
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        get_res = yield terminal_rpc.send_j13(imei)
        if get_res["status"] == error_codes.EC_SEND_CMD_FAIL:
            logging.warning("add_device_info send_command_j13, fail status:%d",
                            error_codes.EC_SEND_CMD_FAIL)
            res["status"] = error_codes.EC_SEND_CMD_FAIL
            self.res_and_fini(res)
            return
        bind_day = datetime.datetime.combine(
            datetime.date.today(),datetime.time.min)
        cur = datetime.datetime.now()
        last_device_log = yield device_dao.get_log_by_imei_before_time(imei, cur)
        old_calorie = 0
        if last_device_log is not None:
            old_calorie = last_device_log["calorie"]
        pet_id = 0
        try:
            pet_id = yield gid_rpc.alloc_pet_gid()
            yield pet_dao.bind_device(uid, imei, pet_id ,bind_day, old_calorie,x_os_int)
        except pymongo.errors.DuplicateKeyError, e:
            logging.error("AddDeviceInfo,uid:%d add device:imei:%s pet_id:%d has exist", uid, imei, pet_id)
            res["status"] = error_codes.EC_EXIST
            try:
                user_dao = self.settings["user_dao"]
                old_user_info = yield pet_dao.get_pet_info(("uid",),
                                                           device_imei=imei)
                if old_user_info is not None:
                    old_uid = old_user_info.get("uid","")
                    if old_uid == "":
                        logging.error("AddDeviceInfo,uid:%d imei:%s has exist,but can't get the old account: %s",
                                        self.dump_req())
                    else:
                        res["old_account"] = ""
                        info = yield user_dao.get_user_info(old_uid, ("phone_num",))
                        logging.info("AddDeviceInfo,get phone num:%s",info)
                        old_account=str(info.get("phone_num", ""))
                        if old_account is not None and len(old_account)>=9:
                            old_account=old_account[0:3]+"_**_"+old_account[-4:]
                        res["old_account"] = old_account
            except Exception, ee:
                logging.error("AddDeviceInfo, imei has exist but can't get the old account: %s %s",
                                self.dump_req(),
                                self.dump_exp(ee))
            self.res_and_fini(res)
            return

        info = {}
        if imei is not None:
            info["imei"] = imei
        if device_name is not None:
            info["device_name"] = device_name
        old_info= yield device_dao.get_device_info(
            imei, ("sim_deadline",))
        if not (old_info is not None and old_info.get("sim_deadline", "") != ""):
            expire_days = SysConfig.current().get(
            sys_config.SC_SIM_CARD_EXPIRE_DAYS)
            info["sim_deadline"] = datetime.datetime.now() + datetime.timedelta(days=expire_days)
        try:
            yield device_dao.update_device_info(**info)
        except Exception, e:
            logging.warning("AddDeviceInfo, error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

# 成功
        logging.debug("AddDeviceInfo, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
