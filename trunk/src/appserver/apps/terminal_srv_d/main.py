# -*- coding: utf-8 -*-

import traceback
import sys
sys.path.append("../../")

reload(sys)
sys.setdefaultencoding("utf-8")

import time
import getopt
import signal
import tornado
import tornado.options
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado.web import Application, url
from tornado import gen

from terminal_base import conn_mgr2, broadcast, thread_trace
from lib.pyloader import PyLoader
from lib.op_log_dao import OPLogDAO
from lib.new_device_dao import NewDeviceDAO
from lib.pet_dao import PetDAO
import terminal_handler
import http_handlers
import imei_timer
import unreply_msg2
from test_handler import CloseTcp
from lib.msg_rpc import MsgRPC
from lib.sys_config import SysConfig
from lib import sys_config

support_setptitle = True
ptitle = "terminal_srv_d"
verbose = False
logrootdir = "./logs/"
listen_port = 5050
debug = False
http_listen_port = 5052
try:
    import setproctitle
except:
    support_setptitle = False

import logging

logger = logging.getLogger(__name__)
mongo_pyloader = PyLoader("configs.mongo_config")
mongo_conf = mongo_pyloader.ReloadInst("MongoConfig", debug_mode=debug)

# Parse options
#def Usage():
#   print "Usage:  -h  get help"

# Set process title
if support_setptitle:
    setproctitle.setproctitle(ptitle)
else:
    logger.warning(
        "System not support python setproctitle module, please check!!!")

# Init web application
#Init async


@gen.coroutine
def _async_init():
    SysConfig.new(mongo_meta=mongo_conf.global_mongo_meta, debug_mode=debug)
    yield SysConfig.current().open()


if __name__ == '__main__':
    tornado.options.options.logging = "debug"
    tornado.options.parse_command_line()
    conn_mgr = conn_mgr2.ServerConnMgr()
    thread_trace.trace_start("trace.html")
    broadcastor = broadcast.BroadCastor(conn_mgr)
    imei_timer_mgr = imei_timer.ImeiTimer()
    unreply_msg_mgr = unreply_msg2.UnreplyMsgMgr2()
    # no_heart_msg_mgr = noheart_msg.NoHeartMsgMgr()
    IOLoop.current().run_sync(_async_init)
    msg_rpc = MsgRPC(SysConfig.current().get(sys_config.SC_MSG_RPC_URL))

    handler = terminal_handler.TerminalHandler(
        conn_mgr,
        debug,
        imei_timer_mgr,
        op_log_dao=OPLogDAO.new(mongo_meta=mongo_conf.op_log_mongo_meta),
        broadcastor=broadcastor,
        pet_dao=PetDAO.new(mongo_meta=mongo_conf.op_log_mongo_meta),
        new_device_dao=NewDeviceDAO.new(
            mongo_meta=mongo_conf.op_log_mongo_meta),
        msg_rpc=msg_rpc,
        unreply_msg_mgr=unreply_msg_mgr,
        # no_heart_msg_mgr=no_heart_msg_mgr
    )

    conn_mgr.CreateTcpServer("", listen_port, handler)
    webapp = Application(
        [
            (r"/op_log", http_handlers.GetOpLogHandler),
            (r"/send_command", http_handlers.SendCommandHandler),
            (r"/send_command2", http_handlers.SendCommandHandler2),
            (r"/send_command3", http_handlers.SendCommandHandler3),
            (r"/send_command4", http_handlers.SendCommandHandler4),
            (r"/send_command_params", http_handlers.SendParamsCommandHandler),
            (r"/send_commandj03", http_handlers.SendCommandHandlerJ03),
            (r"/send_commandj13", http_handlers.SendCommandHandlerJ13),
            (r"/closesocket_byimei",CloseTcp)
        ],
        autoreload=True,
        debug=True,
        broadcastor=broadcastor,
        msg_rpc=msg_rpc,
        unreply_msg_mgr=unreply_msg_mgr,
        conn_mgr=conn_mgr,
        # no_heart_msg_mgr=no_heart_msg_mgr,
        op_log_dao=OPLogDAO.new(mongo_meta=mongo_conf.op_log_mongo_meta), )

    webapp.listen(http_listen_port)
    imei_timer_mgr.set_on_imeis_expire(handler._OnImeiExpires)
    imei_timer_mgr.start()
    unreply_msg_mgr.set_on_un_reply_msg_retry_func(handler._OnUnreplyMsgsSend)
    # no_heart_msg_mgr.set_on_no_heart_func(handler._OnImeiExpires)
    IOLoop.current().start()
