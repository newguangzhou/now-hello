# -*- coding: utf-8 -*-

import json
import urllib
import logging
import traceback
from lib import error_codes

from terminal_base import terminal_commands
from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler


class PetFind(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnPetFind, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        terminal_rpc = self.settings["terminal_rpc"]
        uid = None
        token = None
        find_status = None
        pet_id = None
        res = {"status": error_codes.EC_SUCCESS}
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            pet_id = int(self.get_argument("pet_id"))
            find_status = int(self.get_argument("find_status"))
        except Exception, e:
            logging.warning("OnPetFind, invalid args, %s, exception %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        if find_status not in (1, 2):
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        # 检查token
        st = yield self.check_token("OnOnPetWalk", res, uid, token)
        if not st:
            return
        info = None
        try:
            info = yield pet_dao.get_user_pets(uid, ("pet_id", "device_imei", "sex", "weight", "pet_no_search_status"))
            if info is None or pet_id != info["pet_id"]:
                logging.warning("OnPetFind, not found, %s", self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return

            imei = info.get("device_imei", None)
            if imei is None:
                logging.warning("OnPetFind, not found, %s", self.dump_req())
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return

            gps_enable = 1 if find_status == 1 else 0
            msg = terminal_commands.Params()
            msg.gps_enable = gps_enable
            if msg.gps_enable == 1:
                msg.report_time = 1
            else:
                msg.report_time = 0

            get_res = yield terminal_rpc.send_command_params(
                imei=imei, command_content=str(msg))

            if get_res["status"] == error_codes.EC_SEND_CMD_FAIL:
                res["status"] = error_codes.EC_SEND_CMD_FAIL
                self.res_and_fini(res)
                return

        except Exception, e:
            logging.warning("OnPetFind, sys_error, %s, exception %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        pet_status = 2 if find_status == 1 else 0

        try:
            yield pet_dao.update_pet_info(pet_id, pet_status=pet_status)
        except Exception, e:
            logging.warning("OnPetFind, error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        if info is not None:
            device_imei = info.get("device_imei", None)
            if device_imei is None:
                logging.warning("UpdatePetInfo, not found, %s",
                                self.dump_req())
                return
            msg = terminal_commands.PetLocation()
            if gps_enable:
                msg.battery_threshold = 0
            else:
                msg.battery_threshold = 25
            # send_weight = float(info.get("weight", 0.0))
            send_weight=15
            # send_sex = int(info.get("sex", 1))
            send_sex=1
            msg.light_flash = ((0, 0), (0, 0))
            msg.pet_weight = "%.2f" % (send_weight)
            msg.pet_gender = send_sex
            logging.info("pet_find send_command_j03 msg:%s", msg)
            get_res = yield terminal_rpc.send_command_params(
                imei=device_imei, command_content=str(msg))

            if get_res["status"] == error_codes.EC_SEND_CMD_FAIL:
                logging.warning("pet find,send_command_params, fail status:%d",
                                error_codes.EC_SEND_CMD_FAIL)

            res["pet_status"] = info.get("pet_no_search_status",0)

        self.res_and_fini(res)




    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
