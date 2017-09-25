# -*- coding: utf-8 -*-
import json
import urllib
import logging
import datetime
import traceback
from lib import error_codes
from terminal_base import terminal_commands
import pymongo
from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

from lib import utils
from lib import sys_config
from lib.sys_config import SysConfig


class AddPetInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("AddPetInfo, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        device_dao = self.settings["device_dao"]
        terminal_rpc = self.settings["terminal_rpc"]
        conf = self.settings["appconfig"]
        gid_rpc = self.settings["gid_rpc"]
        res = {"status": error_codes.EC_SUCCESS}

        uid = None
        nick = None
        logo_url = None
        logo_small_url = None
        birthday = None
        sex = None
        weight = None
        pet_type_id = 1
        description = None
        imei = None
        target_energy = 0
        recommend_energy=0

        try:
            uid = int(self.get_argument("uid"))
            pet_type_id = int(self.get_argument("pet_type_id"))
            token = self.get_argument("token")
            st = yield self.check_token("OnAddPetInfo", res, uid, token)
            if not st:
                return
            imei = self.get_argument("imei",None)
            target_energy = float(self.get_argument("target_energy",0))
            recommend_energy=float(self.get_argument("recommend_energy",0))
            nick = self.get_argument("nick", None)
            logo_url = self.get_argument("logo_url", None)
            logo_small_url = self.get_argument("logo_small_url", None)
            sex = self.get_argument("sex", None)
            if sex is not None:
                sex = int(sex)
            birthday = self.get_argument("birthday", None)
            if birthday is not None:
                birthday = utils.str2date(birthday, "%Y-%m-%d")
                birthday = datetime.datetime(birthday.year, birthday.month,
                                             birthday.day)
            weight = self.get_argument("weight", None)
            if weight is not None:
                weight = float(weight)
            description = self.get_argument("description", None)
        except Exception, e:
            logging.warning("AddPetInfo, invalid args1, %s %s", self.dump_req(),
                            str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        if (sex is not None and sex not in (0,1, 2)) or (
                weight is not None and (weight > 1000 or weight < 0))or (
                        pet_type_id is not None and pet_type_id not in (0,-1, 1, 2)):
            logging.warning("AddPetInfo, invalid args2, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        pet_id = yield gid_rpc.alloc_pet_gid()
        info = {"pet_type_id": pet_type_id,"pet_id":pet_id}
        info["target_energy"] = target_energy
        info["recommend_energy"]=recommend_energy
        if nick is not None:
            info["nick"] = nick
        if logo_url is not None:
            info["logo_url"] = logo_url
        if sex is not None:
            info["sex"] = sex
        if birthday is not None:
            info["birthday"] = birthday
        if logo_small_url is not None:
            info["logo_small_url"] = logo_small_url
        if description is not None:
            info["description"] = description
        if weight is not None:
            info["weight"] = weight

        # get imei
        try:

            pet_info = yield pet_dao.get_user_pets(uid, ("device_imei",))
            if pet_info is not None:
                imei = pet_info.get("device_imei")
                if imei is None:
                    logging.warning("AddPetInfo, error, %s", self.dump_req())
                    res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                    self.res_and_fini(res)
                    return
        except Exception, e:
            logging.warning("AddPetInfo, error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        # # 发给终端
        # if weight is not None and sex is not None:
        #     device_imei = imei
        #     if device_imei is None:
        #         logging.warning("AddPetInfo, not found, %s",
        #                         self.dump_req())
        #         return
        #     msg = terminal_commands.PetLocation()
        #     msg.battery_threshold = 25
        #     send_weight = weight
        #     send_sex = sex
        #     msg.light_flash = ((0, 0),(0, 3))
        #     msg.pet_weight = "%.2f" % (send_weight)
        #     msg.pet_gender = send_sex
        #     logging.info("add_pet_info send_command_j03 msg:%s",msg)
        #
        #     get_res = yield terminal_rpc.send_command_params(
        #         imei=device_imei, command_content=str(msg))
        #
        #     if get_res["status"] == error_codes.EC_SEND_CMD_FAIL:
        #         logging.warning("add_pet_info send_command_params, fail status:%d",
        #                         error_codes.EC_SEND_CMD_FAIL)
        #         res["status"] = error_codes.EC_SEND_CMD_FAIL
        #         self.res_and_fini(res)
        #         return

        try:
            yield pet_dao.update_pet_info_by_uid(uid, **info)
            res["status"] = error_codes.EC_SUCCESS
        except pymongo.errors.DuplicateKeyError, e:
            res["status"] = error_codes.EC_EXIST
            self.res_and_fini(res)
            return
        except Exception, e:
            logging.warning("AddPetInfo, error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        res["pet_id"] = pet_id
        res["recommend_energy"]=recommend_energy
        res["recommend_energy_android"]=str(recommend_energy)

        # 成功
        logging.debug("AddPetInfo, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
