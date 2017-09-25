# -*- coding: utf-8 -*-
import tornado
import socket
import logging
from tornado.tcpserver import TCPServer
from tornado.ioloop import IOLoop
from tornado import gen
from functools import partial
logger = logging.getLogger(__name__)

SEND_STATUS_CLOSED = "closed"
SEND_STATUS_OK = "ok"


class ServerConnDelegate(object):
    def on_close(self, conn_id):
        pass


class Conn(object):
    def __init__(self, stream, address, conn_id, conn_mgr):
        self._stream = stream
        self._address = address
        self._conn_mgr = conn_mgr
        self._conn_id = conn_id
        self._stream.set_close_callback(self._on_close)

    def GetPeer(self):
        return str(self._address)

    def write(self, data):
        return self._stream.write(data)

    def get_conn_id(self):
        return self._conn_id

    def _on_close(self):
        self._conn_mgr.on_close(self._conn_id)

    def close(self):
        self._stream.close()


class ServerConnMgr(TCPServer, ServerConnDelegate):
    def __init__(self, context_arg=None, **args):
        TCPServer.__init__(self, **args)
        self._conns = {}
        self._context_arg = context_arg

    def handle_stream(self, stream, address):
        conn_id = stream.fileno().fileno()
        conn = Conn(stream, address, conn_id, self)
        self._conns[conn_id] = conn
        self._handler.OnOpen(conn_id)
        stream.read_until_close(streaming_callback=partial(
            self._handler.OnData, conn_id))

    def CreateTcpServer(self, address, port, handler):
        self._handler = handler
        return self.listen(port, address)

    @gen.coroutine
    def Send(self, conn_id, data):
        ret = SEND_STATUS_OK
        conn = self.get_conn(conn_id)
        if conn is not None:
            yield conn.write(data)
        else:
            ret = SEND_STATUS_CLOSED
        raise gen.Return(ret)

    def GetConn(self, conn_id):
        return self.get_conn(conn_id)

    def get_conn(self, conn_id):
        return self._conns.get(conn_id, None)

    def on_close(self, conn_id):
        try:
            self._handler.OnClose(conn_id, True)  #
            del self._conns[conn_id]
        except Exception, e:
            logger.exception(e)
