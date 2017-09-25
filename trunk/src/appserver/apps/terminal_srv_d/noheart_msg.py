# -*- coding: utf-8 -*-
import time
import logging
from tornado.ioloop import IOLoop
from simple_timer import SimpleTimer
logger = logging.getLogger(__name__)


class NoHeartMsgMgr:
    def __init__(self,
                 on_no_heart_func,
                 max_count=1,
                 key_expires=600):
        self.on_no_heart_func = on_no_heart_func
        self.timer = SimpleTimer(self.on_exire_keys)
        self.max_count = max_count
        self.msg_dict = {}
        self.key_expires = key_expires

    def set_on_no_heart_func(self, on_no_heart_func):
        self.on_no_heart_func = on_no_heart_func
        if not self.timer.is_started():
            self.timer.start()

    def add_no_heart_msg(self, imei):
        logger.debug("add_no_heart_msg , imei:%s ", imei)
        count = self.msg_dict.get(imei, None)
        if count is None:
            self.msg_dict[imei] = self.max_count
            self.timer.add_key(imei, self.key_expires)
        else:
            logger.info("on add_no_heart_msg imei:%s exist, will reset the timeout", imei)

    def delete_no_heart_msg(self, imei):
        logger.debug("delete_no_heart_msg ,imei:%s ", imei)

        count = self.msg_dict.get(imei, None)
        if count is None:
            logger.warning("on delete_no_heart_msg  imei:%s  not exist",
                           imei)
        else:
            del self.msg_dict[imei]

    def on_exire_keys(self, keys):
        imeis = []
        for imei in keys:
            count = self.msg_dict.get(imei, None)
            if count is None:
                logger.warning("on on_exire_keys  imei:%s not exist",
                               imei)
                continue

            count = count - 1
            self.msg_dict[imei] = count
            if count <= 0:
                del self.msg_dict[imei]
                imeis.append(imei)
                logger.warning(
                    "on on_exire_keys  imei:%s count:%d need client reconnect",
                    imei, count)
            else:
                self.timer.add_key(imei, self.key_expires)

        if len(imeis) > 0:
            self.on_no_heart_func(imeis)

