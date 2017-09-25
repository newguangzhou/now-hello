# -*- coding: utf-8 -*-
from lib import sorted_set
import time
import logging
from tornado.ioloop import IOLoop

logger = logging.getLogger(__name__)


class SimpleTimer:
    def __init__(self, on_keys_expire_func, check_num=5, check_timeout=1):
        self.dict = sorted_set.SortedSet()
        self.check_timeout = check_timeout
        self.on_keys_expire_func = on_keys_expire_func
        self.check_num = check_num
        self.stared = False

    def set_on_keys_expire(self, on_keys_expire_func):
        self.on_keys_expire_func = on_keys_expire_func

    def add_key(self, key, expires):
        now = int(time.time())
        timeout = now + expires
        self.dict.zadd(key, timeout)
        logger.debug("add key:%s timeout:%d", key, timeout)

    def start(self):
        IOLoop.instance().call_later(self.check_timeout, self.check)
        self.stared = True

    def is_started(self):
        return self.stared

    def dump(self):
        nodes = self.dict.zrevrange(0, -1, True)
        dump_str = ""
        for key, score in nodes:
            dump_str += "key:%s score:%d " % (str(key), score)
        if dump_str != "":
            print dump_str

    def check(self):
        expire_keys = self.get_expire_keys(self.check_num)
        if len(expire_keys) != 0 and self.on_keys_expire_func != None:
            self.on_keys_expire_func(expire_keys)

        IOLoop.instance().call_later(self.check_timeout, self.check)

    def get_expire_keys(self, num):
        key_with_scores = self.dict.zrange(0, num, True)
        now = int(time.time())
        expire_keys = []
        for key, score in key_with_scores:
            if score <= now:
                expire_keys.append(key)
                self.dict.zrem(key)
                logger.debug("zrem key:%s time:%d now:%d", key, score, now)
            else:
                break
        return expire_keys
