# -*- coding: utf-8 -*-
import sys
sys.path.append("../../")
reload(sys)
sys.setdefaultencoding("utf-8")

from tornado import ioloop, gen
from tornado.web import Application

import tornado.options

from lib.pyloader import PyLoader
from lib.op_log_dao import OPLogDAO
from lib.sys_config import SysConfig

from tornado.ioloop import IOLoop

from lib import utils


support_setptitle = True
ptitle = "self_srv_d"


listen_port = 5053
debug = False


try:
    import setproctitle
except:
    support_setptitle = False

import logging
logger = logging.getLogger(__name__)
# Set process title
if support_setptitle:
    setproctitle.setproctitle(ptitle)
else:
    logger.warning(
        "System not support python setproctitle module, please check!!!")


mongo_pyloader = PyLoader("configs.mongo_config")
mongo_conf = mongo_pyloader.ReloadInst("MongoConfig", debug_mode=debug)

@gen.coroutine
def _async_init():
    SysConfig.new(mongo_meta=mongo_conf.global_mongo_meta, debug_mode=debug)
    yield SysConfig.current().open()

class GetOpLogHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        op_log_dao = self.settings["op_log_dao"]
        #ret = {}
        start_time = None
        end_time = None
        try:
            imei = self.get_argument("imei")
            start = self.get_argument("start")
            end = self.get_argument("end", None)
            start_time = utils.str2datetime(start, "%Y-%m-%d %H:%M:%S")
            if end is not None:
                end_time = utils.str2datetime(end, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            self.write("arg error ")
            return

        op_ret = yield op_log_dao.get_log_info(start_time, end_time, imei,
                                               ("imei", "content", "log_time"))
        ret = "<html>"
        for item in op_ret:
            ret += " 【log_time】:%s 【imei】:%s 【content】:%s <br><br>" % (
                utils.date2str(item["log_time"]), item["imei"],
                item["content"])
            #ret
        ret += "</html>"
        self.write(ret)

if __name__ == '__main__':
    tornado.options.options.logging = "debug"
    tornado.options.parse_command_line()
    IOLoop.current().run_sync(_async_init)
    webapp = Application(
        [
            (r"/op_log", GetOpLogHandler),
        ],
        op_log_dao=OPLogDAO.new(mongo_meta=mongo_conf.op_log_mongo_meta),)
    webapp.listen(listen_port)
    IOLoop.current().start()











