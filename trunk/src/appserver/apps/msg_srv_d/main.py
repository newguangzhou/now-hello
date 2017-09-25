# -*- coding: utf-8 -*-

import sys
sys.path.append("../../")

reload(sys)
sys.setdefaultencoding('utf-8')

import setproctitle

from tornado import ioloop, gen
from tornado.web import Application, url

import tornado.options
from tornado.options import define, options

from lib.console import Console
from lib.pyloader import PyLoader

from lib.auth_dao import AuthDAO

from sms_ymrt import YMRTSMS
from sms_nexmo import NEXMOSMS
from mipush import MIPush
from mipush2 import MiPush2
from sms_dayu import send_verify,send_message
import handlers

define("debug_mode", 0, int,
       "Enable debug mode, 1 is local debug, 2 is test, 0 is disable")
define("port", 9200, int, "Listen port, default is 9200")
define("address", "0.0.0.0", str, "Bind address, default is 127.0.0.1")
define("console_port", 9210, int, "Console listen port, default is 9210")

# Parse commandline
tornado.options.parse_command_line()

# Init pyloader
pyloader = PyLoader("config")
conf = pyloader.ReloadInst("Config")

mongo_pyloader = PyLoader("configs.mongo_config")
mongo_conf = mongo_pyloader.ReloadInst("MongoConfig",
                                       debug_mode=options.debug_mode)

# Set process title
setproctitle.setproctitle(conf.proctitle)

# # Init sms
# sms_sender = NEXMOSMS(pyloader)

# Init web application
webapp = Application(
    [
        (r"/msg/send_sms", handlers.SendSMS),
        (r"/msg/send_verify_code", handlers.SendVerify),
        (r"/msg/push_android", handlers.PushAndrod),
        (r"/msg/push_all", handlers.PushAll),
        (r"/msg/push_ios", handlers.PushIOS),
        (r"/msg/push", handlers.Push)
    ],
    autoreload=True,
    pyloader=pyloader,
    appconfig=conf,
    sms_registered=True,
    auth_dao=AuthDAO.new(mongo_meta=mongo_conf.auth_mongo_meta),
    sms_sender=send_message,
    verify_sender=send_verify,
    xiaomi_push2= MiPush2(conf.mipush_appsecret_android, conf.mipush_pkg_name,
                          conf.mipush_appsecret_ios, conf.mipush_bundle_id, True),
    xiaomi_push=MIPush(conf.mipush_host, conf.mipush_appsecret_android,
                       conf.mipush_pkg_name))


class _UserSrvConsole(Console):
    def handle_cmd(self, stream, address, cmd):
        if len(cmd) == 1 and cmd[0] == "quit":
            self.send_response(stream, "Byte!")
            return False
        elif len(cmd) == 0:
            pass
        elif len(cmd) == 1 and cmd[0] == "reload-config":
            conf = self.pyld.ReloadInst("Config")
            webapp.settings["appconfig"] = conf
            mipush = MIPush(conf.mipush_host, conf.mipush_appsecret,
                           conf.mipush_pkg_name)
            webapp.settings["xiaomi_push"] = mipush
            self.send_response(stream, "done")
        else:
            self.send_response(stream, "Invalid command!")
        return True

# Init console
console = _UserSrvConsole()
console.bind(options.console_port)
console.start()

# Run web app loop
webapp.listen(options.port, options.address, xheaders=True)
ioloop.IOLoop.current().start()
