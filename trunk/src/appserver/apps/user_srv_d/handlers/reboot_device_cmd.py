# -*- coding: utf-8 -*-
import json
import urllib
import logging
import traceback
from lib import error_codes

from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler
from terminal_base import terminal_commands

from lib import sys_config
from lib.sys_config import SysConfig


class RebootDeviceCmd(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("coroutine, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        terminal_rpc = self.settings["terminal_rpc"]
        conf = self.settings["appconfig"]
        res = {"status": error_codes.EC_SUCCESS}

        uid = None
        pet_id = -1
        target_step = None
        imei = None

        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            st = yield self.check_token("OnSetTargetStep", res, uid, token)
            if not st:
               return

            info = yield pet_dao.get_user_pets(uid, ("pet_id", "device_imei"))
            if info is None:
                logging.warning("RebootDeviceCmd, not found, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            imei = info.get("device_imei", None)
            pet_id = info.get("pet_id", None)
            if imei is None or pet_id is None:
                logging.warning("RebootDeviceCmd, not found, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return


        except Exception, e:
            logging.warning("RebootDeviceCmd, invalid args, %s %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        # 重启
        get_res = yield terminal_rpc.send_command_params(
            imei=imei, command_content=str(terminal_commands.TermimalReboot()))
        if get_res["status"] == error_codes.EC_SEND_CMD_FAIL:
            logging.warning("send_command_params reboot, fail status:%d",
                            error_codes.EC_SEND_CMD_FAIL)
            res["status"] = error_codes.EC_SEND_CMD_FAIL
            self.res_and_fini(res)
            return

        info = {"has_reboot":1,"device_status":0}
        try:
            yield pet_dao.update_pet_info(pet_id, **info)
        except Exception, e:
            logging.warning("RebootDeviceCmd,write database error, %s %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

# 成功
        logging.debug("RebootDeviceCmd, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
