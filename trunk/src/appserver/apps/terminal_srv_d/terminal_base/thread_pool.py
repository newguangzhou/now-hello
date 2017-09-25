# -*- coding: utf-8 -*-

""" 
@biref Thread pool implement
@file thread_pool.py
@author ChenYongqiang
@date 2014-12-04
"""

import threading
import sys
import random
import traceback
import time

import logger


class Watcher:
    def OnInit(self, thread):
        pass

    def OnRun(self, thread):
        pass

    def OnStop(self, thread):
        pass

    def OnMsg(self, thread, msg):
        pass

    def OnTimer(self, thread, tick):
        pass


class Thread(threading.Thread):
    def __init__(self, pool):
        threading.Thread.__init__(self)

        self.pool = pool
        self.cond = threading.Condition()
        self.msgq = []

    def run(self):
        self.pool.InvokeWatchers(1, self)

        while True:
            self.cond.acquire()
            while len(self.msgq) <= 0:
                self.cond.wait(0.1)
                self.pool.InvokeWatchers(4, self, tick=time.time())
            m = self.msgq.pop(0)
            if m is None:
                break
            else:
                self.pool.InvokeWatchers(3, self, msg=m)
            self.cond.release()

        self.pool.InvokeWatchers(2, self)

    def Post(self, msg):
        self.cond.acquire()
        self.msgq.append(msg)
        self.cond.notify()
        self.cond.release()


class ThreadPool:
    def __init__(self, count=10, thread_type=None):
        self.thread_type = thread_type
        if thread_type is None:
            self.thread_type = Thread
        self.count = count
        self.watchers = []
        self.threads = []
        self.roundrobin_tick = 0

    def Open(self):
        for i in range(0, self.count):
            th = self.thread_type(self)
            self.InvokeWatchers(0, th)
            self.threads.append(th)
            th.start()

    def StopAll(self):
        for th in self.threads:
            th.Post(None)

    def GetByRandom(self):
        return self.threads[random.randint(0, len(self.threads) - 1)]

    def GetByRoundRobin(self):
        self.roundrobin_tick += 1
        return self.threads[((len(self.threads) + self.roundrobin_tick) % len(self.threads))]

    def Watch(self, watcher):
        self.watchers.append(watcher)

    def InvokeWatchers(self, type, thread, **args):
        try:
            for v in self.watchers:
                if 0 == type:  # Init
                    v.OnInit(thread)
                elif 1 == type:  # Run
                    v.OnRun(thread)
                elif 2 == type:  # Stop
                    v.OnStop(thread)
                elif 3 == type:  # Msg
                    v.OnMsg(thread, args["msg"])
                elif 4 == type:  # Timer
                    v.OnTimer(thread, args["tick"])
        except Exception, e:
            logger.warning("Invoke thread pool watchers error, exp=\"%s\" trace=\"%s\"", str(e), traceback.format_exc())










