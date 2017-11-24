# -*- coding: utf-8 -*-
#import json
#import urllib
import logging
import datetime
import traceback
from lib import error_codes
#from terminal_base import terminal_commands
import pymongo
#from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

from lib import utils
#from lib import sys_config
#from lib.sys_config import SysConfig
from pymongo import errors
from get_base_info import get_base_info
class ChoosePet(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("ChoosePet, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        res = {"status": error_codes.EC_SUCCESS}

        imei = None
        try:
            uid = int(self.get_argument("uid"))
            pet_id = int(self.get_argument("pet_id", -1))
            token = self.get_argument("token")
            st = yield self.check_token("OnChoosePet", res, uid, token)
            if not st:
                return
        except Exception, e:
            logging.warning("ChoosePet, invalid args1, %s %s", self.dump_req(),
                            str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        if pet_id <= 0 :
            res["status"] = error_codes.EC_PET_NOT_EXIST 
            self.res_and_fini(res)
            return

        # get imei
        try:

            pet_info = yield pet_dao.get_pet_info_by_petid(pet_id, ("device_imei",))
            if pet_info is not None :
                imei = pet_info.get("device_imei","")
            if pet_info is None or imei == "" :
                logging.error("ChoosePet fail, uid:%d, , pet_id:%d,  req:%s",
                                uid,imei, pet_id, self.dump_req())
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return
        except Exception, e:
            logging.warning("ChoosePet, error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        try:
            #切换主控设备
            pet_info_now = yield pet_dao.get_pet_info(("pet_id",),uid = uid, choice = 1)
            if pet_info_now:
                old_pet_id = pet_info_now.get("pet_id", -1)
                if old_pet_id > 0:
                    yield pet_dao.update_pet_info(old_pet_id, choice = 0)
            yield pet_dao.update_pet_info(pet_id, choice = 1)
            user_dao = self.settings["user_dao"]
            yield user_dao.update_user_info(uid, choice_petid = pet_id)
            res = yield get_base_info(pet_dao, uid, pet_id)
        except Exception, e:
            logging.warning("ChoosePet,uid:%d imei:%s error, %s %s", uid, imei, self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        # 成功
        logging.debug("ChoosePet,uid:%d pet_id:%d success %s", uid, pet_id, self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
