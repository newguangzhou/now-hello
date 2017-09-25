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
from lib import push_msg
from helper_handler import HelperHandler


class PushMessageCmd(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnPushMessage, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")

        conf = self.settings["appconfig"]
        msg_rpc = self.settings["msg_rpc"]

        res = {"status": error_codes.EC_SUCCESS}

        # 获取请求参数
        uid = None
        push_type = None
        pass_through = None
        try:
            uid = self.get_argument("uid")
            push_type = self.get_argument("type", "in_home")
        except Exception, e:
            logging.warning("OnPushMessage, invalid args, %s %s",
                            self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return
        # payload = ''
        # if push_type == 'in_home':
        #     payload = "宠物现在回家了"
        # elif push_type == 'out_home':
        #     payload = "宠物现在离家了，请确定安全"
        # yield msg_rpc.push_ios_useraccount(uids=str(uid),
        #                                    payload=payload)
        if push_type == "in_home":
                        payload = "宠物现在回家了"
        elif push_type == "out_home":
                      payload = "宠物离开家了"

        yield msg_rpc.push_ios_useraccount(uids=str(uid),
                                            payload=payload,
                                            extra=push_type)

        # msg = push_msg.new_pet_not_home_msg()

        # battery_statue=self.get_argument("battery_statue",0)
        # if battery_statue == '1':
        #   yield msg_rpc.push_android(uids=str(uid),
        #                                   title="小毛球智能提醒",
        #                                  desc="设备低电量，请注意充电",
        #                                 payload=msg,
        #                                pass_through=0)
        # yield msg_rpc.push_ios_useraccount(uids=str(uid),
        #       payload="设备低电量，请注意充电")
        # elif battery_statue == '2':
        #    yield msg_rpc.push_android(uids=str(uid),
        #                                 title="小毛球智能提醒",
        #                                desc="设备超低电量，请注意充电",
        #                               payload=msg,
        #                              pass_through=0)
        #  yield msg_rpc.push_ios_useraccount(uids=str(uid),
        #                                         payload="设备超低电量，请注意充电")


        # try:
        #     yield msg_rpc.push_android(uids=str(uid),
        #                                title="小毛球智能提醒",
        #                                desc="宠物现在离家了，请确定安全",
        #                                payload=msg,
        #                                pass_through=pass_through
        #                                )
        #     if push_type == "alias":
        #         yield msg_rpc.push_ios(uids=str(uid),
        #                                payload=msg
        #                                )
        #     else:
        #         yield msg_rpc.push_ios_useraccount(uids=str(uid),
        #                                         payload="宠物现在回家了")
        # except Exception, e:
        #     logging.warning("OnPushMessage, error, %s %s",
        #                     self.dump_req(), self.dump_exp(e))
        #     res["status"] = error_codes.EC_SYS_ERROR
        #     self.res_and_fini(res)
        #     return
        # 成功
        logging.debug("OnPushmessage, success %s",
                      self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
