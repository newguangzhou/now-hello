# -*- coding: utf-8 -*-
from __future__ import division
import json
import urllib
import logging
import traceback
from lib import error_codes

from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

from lib import utils
from lib import sys_config
from lib.sys_config import SysConfig


class GetActivityInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("GetActivityInfo, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        conf = self.settings["appconfig"]

        res = {"status": error_codes.EC_SUCCESS}

        uid = None
        token = None
        pet_id = -1
        start_date = None
        end_date = None

        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            st = yield self.check_token("GetActivityInfo", res, uid, token)
            if not st:
               return

            pet_id = int(self.get_argument("pet_id", -1))
            start_date = self.get_argument("start_date", "2015-04-12")
            if start_date is not None:
                start_date = utils.str2datetime(start_date + " 00:00:00",
                                                "%Y-%m-%d %H:%M:%S")
            end_date = self.get_argument("end_date", "2015-05-12")
            if end_date is not None:
                end_date = utils.str2datetime(end_date + " 23:59:59",
                                              "%Y-%m-%d %H:%M:%S")
        except Exception, e:
            logging.warning("GetActivityInfo, invalid args, %s",
                            self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        res_info = yield pet_dao.get_sport_info(pet_id, start_date, end_date)

        pet_info = yield pet_dao.get_user_pets(uid,("target_energy","weight","sex"))
        target_amount=0
        weight=15
        sex=1
        if pet_info is not None:
            target_amount = pet_info.get("target_energy",0)
            weight=pet_info.get("weight",15)
            sex=pet_info.get("sex",1)
        #print res_info
        res["data"] = []
        if res_info is not None:
            for item in res_info:
                print item
                date_data = {}
                date_data["date"] = utils.date2str(item["diary"].date())
                date_data["target_amount"] = target_amount
                #date_data["reality_amount"] = '{:.1f}'.format(item["calorie"] /1000)
                date_data["reality_amount"] ='{:.1f}'.format(utils.calorie_transform((item["calorie"] / 1000.0),weight,sex))
                percentage = 0
                if date_data["target_amount"] <= 0:
                    percentage = 0
                else:
                    percentage = int(
                        float(date_data["reality_amount"]) / date_data["target_amount"]
                    * 100)
                date_data["percentage"] = percentage
                date_data["target_amount"] = "%.2f" % date_data["target_amount"]
                res["data"].append(date_data)
        else:
            date_data = {}
            date_data["reality_amount"] =0
            date_data["target_amount"] = target_amount
            date_data["percentage"] = 0
            res["data"].append(date_data)

        # 成功
        logging.debug("GetActivityInfo, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
