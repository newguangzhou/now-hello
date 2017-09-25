# -*- coding: utf-8 -*-
from simple_timer import SimpleTimer
import time
import logging
from tornado.ioloop import IOLoop

logger = logging.getLogger(__name__)


class ImeiTimer:
    def __init__(self, imei_timeout=6 * 60, check_timeout=10, check_num=5):
        self.real_timer = SimpleTimer(None, check_num, check_timeout)
        self.imei_timeout = imei_timeout

    def set_on_imeis_expire(self, on_imeis_expire_func):
        self.real_timer.set_on_keys_expire(on_imeis_expire_func)

    def add_imei(self, imei):
        self.real_timer.add_key(imei, self.imei_timeout)

    def start(self):
        self.real_timer.start()
