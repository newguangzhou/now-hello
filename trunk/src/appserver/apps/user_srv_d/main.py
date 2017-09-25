# -*- coding: utf-8 -*-

import sys
sys.path.append("../../")
sys.path.append("../terminal_srv_d/")
reload(sys)
sys.setdefaultencoding('utf-8')

#import setproctitle
from tornado import ioloop, gen
from tornado.web import Application, url

import tornado.options
from tornado.options import define, options

from lib.console import Console
from lib.pyloader import PyLoader
from lib.auth_dao import AuthDAO
from lib.user_dao import UserDAO
from lib.pet_dao import PetDAO
from lib.global_dao import GlobalDAO
#from lib.device_dao import DeivceDAO
from lib.sys_config import SysConfig
from lib import sys_config
from lib.new_device_dao import NewDeviceDAO

from lib.gid_rpc import GIDRPC
from lib.msg_rpc import MsgRPC
from lib.terminal_rpc import TerminalRPC
support_setptitle = True
try:
    import setproctitle
except:
    support_setptitle = False

import handlers

define("debug_mode", 0, int,
       "Enable debug mode, 1 is local debug, 2 is test, 0 is disable")
define("port", 9100, int, "Listen port, default is 9100")
define("address", "0.0.0.0", str, "Bind address, default is 127.0.0.1")
define("console_port", 9110, int, "Console listen port, default is 9110")

# Parse commandline
tornado.options.parse_command_line()

# Init pyloader
pyloader = PyLoader("config")
conf = pyloader.ReloadInst("Config")

mongo_pyloader = PyLoader("configs.mongo_config")
mongo_conf = mongo_pyloader.ReloadInst("MongoConfig",
                                       debug_mode=options.debug_mode)

# Set process title
if support_setptitle:
    setproctitle.setproctitle(conf.proctitle)

# Init web application
webapp = Application(
    [
        (r"/user/get_verify_code", handlers.GetVerifyCode),
        (r"/user/push_message_cmd", handlers.PushMessageCmd),
        (r"/user/login", handlers.Login),
        (r"/user/register", handlers.Register),
        (r"/user/logout", handlers.Logout),
        (r"/user/regen_token", handlers.RegenToken),
        (r"/user/set_home_wifi", handlers.SetHomeWifi),
        (r"/user/set_home_location", handlers.SetHomeLocation),
        (r"/user/get_base_infomation", handlers.GetBaseInfo),
        (r"/user/suggest",handlers.Suggest),
        (r"/pet/location", handlers.PetLocation),
        (r"/pet/location_test", handlers.PetLocation2),
        (r"/pet/walk", handlers.PetWalk),
        (r"/pet/find", handlers.PetFind),
        (r"/pet/get_pet_type_info", handlers.PetTypeInfo),
        (r"/pet/get_pet_info", handlers.GetPetInfo),
        (r"/pet/get_pet_status", handlers.GetPetStatusInfo),
        (r"/pet/add_pet_info", handlers.AddPetInfo),
        (r"/pet/update_pet_info", handlers.UpdatePetInfo),
        (r"/pet/healthy/get_activity_info", handlers.GetActivityInfo),
        (r"/pet/healthy/get_sleep_info", handlers.GetSleepInfo),
        (r"/pet/healthy/summary", handlers.Summary),
        (r"/pet/healthy/set_sport_info", handlers.SetTargetStep),
        (r"/pet/activity", handlers.PetActivity),
        (r"/device/add_device_info", handlers.AddDeviceInfo),
        (r"/device/get_info", handlers.GetDeviceInfo),
        (r"/device/remove_device_info", handlers.RemoveDeviceInfo),
        (r"/device/set_sim_info", handlers.SetSimInfo),
        (r"/device/switch_light", handlers.SwitchLight),
        (r"/device/get_light_status", handlers.GetDeviceSwitchLightStatus),
        (r"/device/send_get_wifi_list_cmd", handlers.SendGetWifiListCmd),
        (r"/device/get_wifi_list", handlers.GetWifiList),
        (r"/device/reboot_device_cmd", handlers.RebootDeviceCmd),
        (r"/user/agree_policy", handlers.AgreePolicy),
        (r"/device/get_device_status",handlers.GetPetStatusInfo),
        (r"/app/get_config",handlers.AppConfig),
    ],
    autoreload=True,
    pyloader=pyloader,
    user_dao=UserDAO.new(mongo_meta=mongo_conf.user_mongo_meta),
    global_dao=GlobalDAO.new(mongo_meta=mongo_conf.global_mongo_meta),
    auth_dao=AuthDAO.new(mongo_meta=mongo_conf.auth_mongo_meta),
    pet_dao=PetDAO.new(mongo_meta=mongo_conf.pet_mongo_meta),
    device_dao=NewDeviceDAO.new(mongo_meta=mongo_conf.pet_mongo_meta),

    appconfig=conf, )


class _UserSrvConsole(Console):
    def handle_cmd(self, stream, address, cmd):
        if len(cmd) == 1 and cmd[0] == "quit":
            self.send_response(stream, "Byte!")
            return False
        elif len(cmd) == 0:
            pass
        elif len(cmd) == 1 and cmd[0] == "reload-config":
            newconf = pyloader.ReloadInst("Config")
            webapp.settings["appconfig"] = newconf
            webapp.settings["gid_rpc"] = GIDRPC(newconf.gid_rpc_url)
            self.send_response(stream, "done")
        elif len(cmd) == 1 and cmd[0] == "reload-sysconfig":
            webapp.settings["sysconfig"].reload()
            self.send_response(stream, "done")
        else:
            self.send_response(stream, "Invalid command!")
        return True

# Init console
console = _UserSrvConsole()
console.bind(options.console_port, "127.0.0.1")
console.start()


# Init async
@gen.coroutine
def _async_init():
    SysConfig.new(mongo_meta=mongo_conf.global_mongo_meta,
                  debug_mode=options.debug_mode)
    yield SysConfig.current().open()
    webapp.settings["gid_rpc"] = GIDRPC(SysConfig.current().get(
        sys_config.SC_GID_RPC_URL))
    webapp.settings["msg_rpc"] = MsgRPC(SysConfig.current().get(
        sys_config.SC_MSG_RPC_URL))
    webapp.settings["terminal_rpc"] = TerminalRPC(SysConfig.current().get(
        sys_config.SC_TERMINAL_RPC_URL))


ioloop.IOLoop.current().run_sync(_async_init)

# Run web app loop
webapp.listen(options.port, options.address, xheaders=True)
ioloop.IOLoop.current().start()
