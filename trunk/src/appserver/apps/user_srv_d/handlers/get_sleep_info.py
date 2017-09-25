# -*- coding: utf-8 -*-
from __future__ import division

import json
import urllib
import logging
import traceback
from lib import error_codes
import datetime
from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler
from lib import utils
from lib import sys_config
from lib.sys_config import SysConfig


class GetSleepInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("GetSleepInfo, %s", self.dump_req())

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
            st = yield self.check_token("GetSleepInfo", res, uid, token)
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
            logging.warning("GetSleepInfo, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        try:
            info = yield pet_dao.get_user_pets(uid, ("pet_id", "device_imei"))
            if info is None or pet_id != info["pet_id"]:
                logging.warning("GetSleepInfo, not found, %s", self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return

            res_info = yield pet_dao.get_sleep_info(pet_id, start_date,
                                                    end_date)
            res["data"] = []
            if res_info is not None:
                sleep_date_info = {}
                for item in res_info:
                    date = utils.date2str(item["begin_time"].date())
                    begin_time = item["begin_time"]
                    end_time = item["begin_time"] + datetime.timedelta(
                        seconds=item["total_secs"])
                    quality = item["quality"]
                    tmp = sleep_date_info.get(date, None)
                    if tmp is None:
                        sleep_date_info[date] = {1: [], 2: []}
                    sleep_date_info[date][quality].append(
                        (begin_time, end_time))
                for k, v in sleep_date_info.items():
                    date_data = {}
                    deep_delta = datetime.timedelta(seconds=0)
                    light_delta = datetime.timedelta(seconds=0)
                    if len(v[1]) != 0:
                        deeps = utils.merge(v[1])

                        for item in deeps:
                            tmp = item[1] - item[0]
                            deep_delta += tmp
                    if len(v[2]) != 0:
                        lights = utils.merge(v[2])
                        for item in lights:
                            tmp = item[1] - item[0]
                            light_delta += tmp

                    date_data["date"] = k
                    date_data["deep_sleep"] = '{:.1f}'.format(
                        deep_delta.total_seconds() / 3600)
                    date_data["light_sleep"] = '{:.1f}'.format(
                        light_delta.total_seconds() / 3600)
                    res["data"].append(date_data)
            else:
                date_data = {}
                date_data["deep_sleep"] = 0
                date_data["light_sleep"] = 0
                res["data"].append(date_data)

        except Exception, e:
            logging.error("GetSleepInfo, error, %s %s", self.dump_req(),
                          self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        #import random
        #from datetime import date, timedelta
        #temp_start_date = start_date
        #while temp_start_date <= end_date:
        #    deep = round(random.uniform(5, 9), 1)
        #    light = round(9.0- deep,1)
        #    data = {}
        #    data["date"] = temp_start_date.strftime("%Y-%m-%d")
        #    data["deep_sleep"] = str(deep)
        #    data["light_sleep"] = str(light)
        #    res["data"].append(data)
        #    temp_start_date += timedelta(days=1)
        # 成功
        logging.debug("GetSleepInfo, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
