# -*- coding: utf-8 -*-

import threading
import logging 
import time
import traceback
import random

from tornado import ioloop, gen
from tornado.concurrent import Future 

from concurrent.futures import ThreadPoolExecutor

import hashring
import redis
import rediscluster

class RedisMetaException(Exception):
    def __init__(self, message):
        self._message = message
        
    def __str__(self):
        return self._message
    
class RedisMeta:
    def __init__(self, *args, **kwargs):
        self.host = "127.0.0.1"
        self.port = 6379
        self.cluster = False
        self.passwd = None
        self.readonly = False
        
        if kwargs.has_key("host"):
            self.host = kwargs["host"]
        
        if kwargs.has_key("port"):
            self.port = kwargs["port"]
        
        if kwargs.has_key("passwd"):
            self.passwd = kwargs["passwd"]
            
        if kwargs.has_key("readonly"):
            self.readonly = kwargs["readonly"]
        
        if kwargs.has_key("cluster"):
            self.cluster = kwargs["cluster"]
        
        self._identity = "%s:%d" % (self.host, self.port)
    
    def get_identity(self):
        return self._identity
    
    def __str__(self):
        return str({"host":self.host, "port":self.port, "passwd":self.passwd, "readonly":self.readonly})
    
class RedisInstMgr:
    def __init__(self, *args, **kwargs):
        tmp = None 
        if len(args) > 0:
            tmp = args[0]
        else:
            tmp = kwargs["metas"]
        
        self._metas = {}
        self._threads = {}
        self._readonly_threads = {}
        for meta in tmp:
            self._metas[meta.get_identity()] = meta
            
            thread = ThreadPoolExecutor(3)
            thread.meta = meta  
            
            if meta.readonly:
                self._readonly_threads[meta.get_identity()] = thread
            else:
                self._threads[meta.get_identity()] = thread 
        
        self._hashring = hashring.HashRing(self._threads.keys())
        self._readonly_hashring = hashring.HashRing(self._readonly_threads.keys())
        
        self._th_local = threading.local()
    
    def _inner_callback(self, **kwargs):
        __thread_obj = kwargs["__thread_obj"]
        __real_callback = kwargs["__real_callback"]
        
        if not hasattr(self._th_local, "redis_clt"):
            meta = __thread_obj.meta
            if meta.cluster:
                self._th_local.redis_clt = redis.RedisCluster(host = meta.host, port = meta.port, password = meta.passwd)
                logging.info("Init redis cluster success, info=\"%s\"", meta.get_identity())
            else:
                self._th_local.redis_clt = redis.Redis(host = meta.host, port = meta.port, password = meta.passwd)
                logging.info("Init redis success, info=\"%s\"", meta.get_identity())
            
            self._th_local.identity = meta.get_identity()
        
        ret = __real_callback(**kwargs)
        return ret
        
    @gen.coroutine
    def submit(self, inst, callback, **kwargs):    
        kwargs["__thread_obj"] = inst 
        kwargs["__real_callback"] = callback
        
        ret = yield inst.submit(self._inner_callback, **kwargs)
        raise gen.Return(ret)
    
    """
    This method must be called in thread 
    """
    def current_client(self):
        return self._th_local.redis_clt
    
    def get_inst_by_random(self, readonly = False):
        tmp = self._threads.keys()
        if readonly:
            tmp = self._readonly_threads.keys()
        
        id = None
        n = len(tmp)
        if n == 0:
            return None
        elif n == 1: 
            id = tmp[0]
        else:
            id = tmp[random.randint(0, n - 1)]
        
        if readonly:
            return self._readonly_threads[id]
        else:
            return self._threads[id]
    
    def get_inst_by_hashring(self, key, readonly = False):
        ring = self._hashring
        if readonly:
            ring = self._readonly_hashring
        tmp = ring.get_node(key)
        if not tmp:
            return None
        else:
            if readonly:
                return self._readonly_threads[tmp]
            else:
                return self._threads[tmp]
    