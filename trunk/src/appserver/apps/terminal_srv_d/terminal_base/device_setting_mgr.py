# -*- coding: utf-8 -*-
#from lib import terminal_rpc
import datetime
import terminal_commands
from tornado import gen
import logging
from lib import error_codes
#import traceback
logger = logging.getLogger(__name__)
class DeviceSetting:
    #设置对象，包含一个dict，格式如:{"GPS":2,"report_time":0,"update_time":"2017-11-01 12:00:00"}
    def __init__(self, imei, dao, terminal_rpc):
        self._imei = imei
        self._dao = dao
        self.params = terminal_commands.Params()
        self._terminal_rpc = terminal_rpc
        self.reload()
        self._setting = ""
    def __getitem__(self, key):
        return self.params[key]
    def __setitem__(self, key, value ):
        self.params[key] = value
    @gen.coroutine
    def reload(self):
        res = yield self._dao.get_device_info(self._imei, ["setting","update_time"])
        self._setting = res.get("setting","005,0#0#0#0#0##0#0#0#0#5000")
        if self.parse(self._setting):
            print "reload imei:",self._imei," setting=",self._setting
            #traceback.print_stack()
            raise gen.Return(True)
        else:
            raise gen.Return(False)

    @gen.coroutine
    def save(self):
        new_setting = unicode(str(self.params))
        logger.info("save imei:%s ,old setting:%s new setting:%s" ,self._imei ,self._setting, new_setting)
        if new_setting == self._setting:
            return
        self.params["update_time"] = datetime.datetime.now()
        res = yield self._terminal_rpc.send_command_params(imei=self._imei, command_content=str(new_setting))
        if res["status"] == error_codes.EC_SUCCESS:
            self._setting = new_setting
            yield self._dao.update_device_info(self._imei, setting=new_setting, update_time = self.params["update_time"])
    def parse(self, setting):
        try:
            self.params.Parse(setting)
        except Exception, e:
            return False
        else:
            return True

    def __str__(self):
        return str(self.params)

class DeviceSettingMgr:
    def __init__(self, dao, terminal_rpc ):
        self.devices={}
        self._dao = dao
        self._terminal_rpc = terminal_rpc
    def __getitem__(self, imei):
        #返回一个DeviceSetting对象
        if(self.devices.has_key(imei)):
            return self.devices[imei]
        else:
            device = DeviceSetting(imei, self._dao, self._terminal_rpc)
            self.devices[imei] = device
            return device



