# -*- coding: utf-8 -*-
#from lib import terminal_rpc
import datetime
import terminal_commands
from tornado import gen
import logging
#import traceback
logger = logging.getLogger(__name__)
class DeviceSetting:
    #设置对象，包含一个dict，格式如:{"GPS":2,"report_time":0,"update_time":"2017-11-01 12:00:00"}
    def __init__(self, imei, dao ):
        self._imei = imei
        self._dao = dao
        self._params = terminal_commands.Params()
        self._setting = ""
    def __getitem__(self, key):
        return self._params[key]
    def __setitem__(self, key, value ):
        self._params[key] = value
    @gen.coroutine
    def load(self):
        res = yield self._dao.get_device_info(self._imei, ["setting","update_time"])
        self._setting = res.get("setting","005,0#0#0#0#0##0#0#0#0#5000")
	logger.debug("imei:%s load setting:%s,self._setting:%s",self._imei, res, self._setting)
        if self.parse(self._setting):
	    logger.debug("imei:%s parse setting:%s success",self._imei, self._setting)
            #traceback.print_stack()
            raise gen.Return(True)
        else:
	    logger.debug("imei:%s parse setting:%s fail",self._imei, self._setting)
            raise gen.Return(False)

    @gen.coroutine
    def save(self):
        new_setting = unicode(str(self._params))
        logger.info("save imei:%s ,old setting:%s new setting:%s" ,self._imei ,self._setting, new_setting)
        if new_setting == self._setting:
            return
        self._params["update_time"] = datetime.datetime.now()
        self._setting = new_setting
        yield self._dao.update_device_info(self._imei, setting=new_setting, update_time = self._params["update_time"])
    def parse(self, setting):
        try:
            self._params.Parse(setting)
        except Exception, e:
            return False
        else:
            return True
    def __str__(self):
        logger.debug("__str__, imei:%s setting :%s param:%s",self._imei, self._setting, self._params)
        return str(self._params)

class DeviceSettingMgr:
    def __init__(self, dao ):
        self.devices={}
        self._dao = dao
    def get_device_setting(self, imei):
        device = DeviceSetting(imei, self._dao )
        return device



