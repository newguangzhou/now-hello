# -*- coding: utf-8 -*-

import logging
from tornado import gen
logger = logging.getLogger(__name__)
import time
from conn_mgr2 import SEND_STATUS_CLOSED


class BroadException(Exception):
    def __init__(self, message, *args):
        self._msg = message % tuple(args)

    def __str__(self):
        return self._msg


class BroadCastor(object):
    def __init__(self, *args, **kwargs):
        if len(args) > 0:
            self.conn_mgr = args[0]
        else:
            self.conn_mgr = kwargs["conn_mgr"]
        self._conn_imei_dict = {}
        self._imei_conn_dict = {}
        #self._imei_timestamp_dict = {}

    def register_conn(self, conn_id, imei):
        logger.info("register_conn conn_id:%d, imei:%s", conn_id, imei)
        exist = self._imei_conn_dict.has_key(imei)
        self._imei_conn_dict[imei] = conn_id
        self._conn_imei_dict[conn_id] = imei
        #self._imei_timestamp_dict[imei] = int(time.time())
        return exist

    def un_register_conn(self, conn_id):
        logger.info("un_register_conn conn_id:%d ", conn_id)

        imei = self._conn_imei_dict.get(conn_id, None)
        if imei != None:
            try:
                del self._conn_imei_dict[conn_id]
                tmp_conn_id = self._imei_conn_dict.get(imei, None)
                if tmp_conn_id is not None and tmp_conn_id == conn_id:
                    del self._imei_conn_dict[imei]
            except Exception, e:
                logger.exception(
                    "on un_register_conn conn_id:%d imei:%s exception:%s",
                    conn_id, imei, str(e))

    def get_imei_by_conn(self, conn_id):
        imei = self._conn_imei_dict.get(conn_id, None)
        return imei
    def get_connid_by_imei(self,imei):
        connid=self._imei_conn_dict.get(imei,None)
        return connid

    @gen.coroutine
    def send_msg_multicast(self, imeis, data):
        ret = True
        for imei in imeis:
            conn_id = self._imei_conn_dict.get(imei, None)
            if conn_id == None:
                ret = False
                logger.error("on send_msg_multicast not found imei:%s", imei)
            else:
                tmp = yield self.conn_mgr.Send(conn_id, data)
                logger.info("on send_msg_multicast imei:%s send res:%s", imei,
                            str(tmp))
                if tmp == SEND_STATUS_CLOSED:
                    ret = False
        raise gen.Return(ret)
