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
from lib.files_dao import FilesDAO
from lib.user_dao import UserDAO
from lib.sys_config import SysConfig

import handlers.user.upload_logo
import handlers.get

define("debug_mode", 0, int, "Enable debug mode, 1 is local debug, 2 is test, 0 is disable")
define("port", 9700, int, "Listen port, default is 9700")
define("address", "0.0.0.0", str, "Bind address, default is 127.0.0.1")
define("console_port", 9710, int, "Console listen port, default is 9710")

# Parse commandline
tornado.options.parse_command_line()

# Init pyloader
pyloader = PyLoader("config")
conf = pyloader.ReloadInst("Config")

mongo_pyloader = PyLoader("configs.mongo_config")
mongo_conf = mongo_pyloader.ReloadInst("MongoConfig", debug_mode = options.debug_mode)

# Set process title
setproctitle.setproctitle(conf.proctitle)

# Init web application
webapp = Application(
        [
         (r"/file/pet/upload_logo", handlers.user.upload_logo.UploadLogo),
         (r"/file/get", handlers.get.Get),
        ],
        autoreload = False,
        pyloader = pyloader,
        files_dao = FilesDAO.new(mongo_meta = mongo_conf.files_mongo_meta),
        auth_dao = AuthDAO.new(mongo_meta = mongo_conf.auth_mongo_meta),
        user_dao = UserDAO.new(mongo_meta = mongo_conf.user_mongo_meta),
        appconfig = conf,
    )

class _UserSrvConsole(Console):
    def handle_cmd(self, stream, address, cmd):
        if len(cmd) == 1 and cmd[0] == "quit":
            self.send_response(stream,"Byte!")
            return False
        elif len(cmd) == 0:
            pass
        elif len(cmd) == 1 and cmd[0] == "reload-config":
            newconf = pyloader.ReloadInst("Config")
            webapp.settings["appconfig"] = newconf
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
    SysConfig.new(mongo_meta = mongo_conf.global_mongo_meta, debug_mode = options.debug_mode)
    yield SysConfig.current().open()
ioloop.IOLoop.current().run_sync(_async_init)

# Run web app loop
webapp.listen(options.port, options.address, xheaders = True)
ioloop.IOLoop.current().start()
