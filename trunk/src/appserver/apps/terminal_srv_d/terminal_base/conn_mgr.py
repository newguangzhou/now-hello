# -*- coding: utf-8 -*-
""" 
@biref Connection manager base on epoll
@file connmgr.py
@author ChenYongqiang
@date 2014-12-04
"""

import select
import os
import socket
import errno
import threading
import traceback

import logger

TCP_SERVER_CONN = 1
TCP_CLIENT_CONN = 2
TCP_SVC_CONN = 3


def ParseServerAddress(address):
    ret = None
    tmp = address.split(":")
    if len(tmp) == 2:
        port = None
        try:
            port = tmp[1]
        except:
            pass
        if port:
            ret = (tmp[0], port)

    return ret


class Conn:
    def __init__(self):
        self.ip = None
        self.port = None
        self.type = None
        self.sock = None
        self.wbuff = None
        self.wbuff_max = None
        self.data = None
        self.handler = None

    def __str__(self):
        if self.type == TCP_SERVER_CONN:
            return "listen on:%s:%u" % (self.ip, self.port)
        elif self.type == TCP_CLIENT_CONN:
            return "connect to:%s:%u" % (self.ip, self.port)
        else:
            return "accpet conn:%s:%u" % (self.ip, self.port)

    def GetPeer(self):
        return "%s:%u" % (self.ip, self.port)


class Event:
    def Do(self, conn_mgr):
        pass


class CloseConnEvent(Event):
    def __init__(self, conn_id, is_eof):
        self._conn_id = conn_id
        self._is_eof = is_eof

    def Do(self, conn_mgr):
        conn_mgr._InnerCloseConn(self._conn_id, self._is_eof)


class EpollConnMgr:
    def __init__(self, **kwargs):
        self._epoll_fd = select.epoll()
        self._fd2conn = {}

        # Init loop event
        self._events = []
        self._event_rd_fd, self._event_wr_fd = os.pipe()
        self._event_wrbuff = None
        self._epoll_fd.register(self._event_rd_fd, select.EPOLLIN)

    def __GetConnHandler(self, conn):
        ret = conn.handler
        if not ret:
            ret = self
        return ret

    def OnOpen(self, id):
        return True

    def OnClose(self, id, is_eof):
        pass

    def OnError(self, id, errno):
        pass

    def OnData(self, id, data):
        return True

    def OnWrite(self, id, size):
        return True

    def GetConn(self, id):
        if self._fd2conn.has_key(id):
            return self._fd2conn[id]
        else:
            return None

    def GetConns(self):
        return self._fd2conn

    def Send(self, id, data):
        if not self._fd2conn.has_key(id):
            logger.warning("Can not send data to conn, not exist, id=%u", id)
            return None

        conn = self._fd2conn[id]
        ret = 0
        try:
            ret = conn.sock.send(data)
        except socket.error, msg:
            if msg.errno != errno.EAGAIN:
                logger.warning(
                    "send data to conn error, conninfo=\"%s\" exp=\"%s\" trace=\"%s\"",
                    str(conn), str(msg), traceback.format_exc())
                self.CloseConn(id)
                return None
            else:
                if conn.wbuff is None:
                    conn.wbuff = ""
                if len(conn.wbuff) + len(data) > conn.wbuff_max:
                    logger.warning(
                        "Send data to conn error, write buffer overflow, conninfo=\"%s\"",
                        str(conn))
                    self.CloseConn(id)
                    return None
                conn.wbuff += data
                self._epoll_fd.modify(id, select.EPOLLIN | select.EPOLLERR |
                                      select.EPOLLOUT)
        return ret

    def CreateTcpServer(self,
                        bind_ip,
                        bind_port,
                        handler=None,
                        wbuff_max=2048):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_ip, bind_port))
        sock.setblocking(0)
        sock.listen(10)

        conn = Conn()
        conn.ip = bind_ip
        conn.port = bind_port
        conn.type = TCP_SERVER_CONN
        conn.sock = sock
        conn.handler = handler
        conn.wbuff_max = wbuff_max

        self._epoll_fd.register(sock.fileno(), select.EPOLLIN |
                                select.EPOLLERR)
        self._fd2conn[sock.fileno()] = conn

        return conn

    def CreateTcpClient(self, host, port, handler=None, wbuff_max=2048):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setblocking(0)

        try:
            sock.connect((host, port))
        except socket.error, msg:
            if msg.errno != errno.EAGAIN and msg.errno != errno.EINPROGRESS:
                raise msg

        conn = Conn()
        conn.ip = host
        conn.port = port
        conn.type = TCP_CLIENT_CONN
        conn.sock = sock
        conn.handler = handler
        conn.wbuff_max = wbuff_max

        self._epoll_fd.register(sock.fileno(), select.EPOLLIN | select.EPOLLERR
                                | select.EPOLLOUT)
        self._fd2conn[sock.fileno()] = conn

        return conn

    def RegisterEvent(self, ev):
        mutex = threading.Lock()
        mutex.acquire()
        try:
            os.write(self._event_wr_fd, "1")
        except Exception, e:
            logger.error(
                "Register event error, this is bug bug!!, exp=\"%s\" trace=\"%s\"",
                str(e), traceback.format_exc())
        self._events.append(ev)
        mutex.release()

    def _InnerCloseConn(self, fd, is_eof=False):
        if self._fd2conn.has_key(fd):
            conn = self._fd2conn[fd]
            try:
                self.__GetConnHandler(conn).OnClose(fd, is_eof)
            except Exception, e:
                logger.warning("OnClose error, exp=\"%s\" trace=\"%s\"",
                               str(e), traceback.format_exc())
            self._epoll_fd.unregister(fd)
            conn.sock.close()
            del self._fd2conn[fd]

    def CloseConn(self, fd, is_eof=False):
        self.RegisterEvent(CloseConnEvent(fd, is_eof))

    def CheckEvents(self, timeout, max_count=500):
        epoll_list = self._epoll_fd.poll(timeout, max_count)

        for fd, events in epoll_list:
            if fd == self._event_rd_fd:  # 是事件管道读句柄
                tmp = None

                # 读取管道数据
                try:
                    tmp = os.read(self._event_rd_fd, 200)
                except Exception, e:
                    logger.error(
                        "Read event read pipe error, bug bug!!, exp=\"%s\" trace=\"%s\"",
                        str(e), traceback.format_exc())
                    return False

                # 处理事件
                assert (len(tmp) <= len(self._events))
                tmp_len = len(tmp)
                for i in range(0, tmp_len):
                    ev = self._events.pop(0)
                    if not ev:
                        return False
                    try:
                        ev.Do(self)
                    except Exception, e:
                        logger.warning(
                            "Do event error, exp=\"%s\" trace=\"%s\"", str(e),
                            traceback.format_exc())
            else:  # 是正常的socket句柄
                if not self._fd2conn.has_key(fd):
                    continue

                conn = self._fd2conn[fd]
                if conn.type == TCP_SERVER_CONN:
                    sock, addr = conn.sock.accept()
                    sock.setblocking(0)

                    tmp = Conn()
                    tmp.ip = addr[0]
                    tmp.port = addr[1]
                    tmp.type = TCP_SVC_CONN
                    tmp.sock = sock
                    tmp.handler = conn.handler
                    tmp.wbuff_max = conn.wbuff_max
                    self._fd2conn[sock.fileno()] = tmp
                    self._epoll_fd.register(sock.fileno(), select.EPOLLIN |
                                            select.EPOLLERR)

                    call_ret = False
                    try:
                        call_ret = self.__GetConnHandler(tmp).OnOpen(
                            sock.fileno())
                    except Exception, e:
                        logger.warning(
                            "OnOpen has exp, exp=\"%s\" trace=\"%s\"", str(e),
                            traceback.format_exc())
                    if not call_ret:
                        self._InnerCloseConn(sock.fileno())
                elif events & select.EPOLLIN:
                    handler = self.__GetConnHandler(conn)
                    data = ""
                    try:
                        data = conn.sock.recv(1024)
                    except socket.error, msg:
                        handler.OnError(fd, msg.errno)
                        self._InnerCloseConn(fd)
                        continue

                    if not data:
                        self._InnerCloseConn(fd, True)
                    else:
                        call_ret = False
                        try:
                            call_ret = handler.OnData(fd, data)
                        except Exception, e:
                            logger.warning(
                                "OnData has exp, exp=\"%s\" trace=\"%s\"",
                                str(e), traceback.format_exc())
                        if not call_ret:
                            self._InnerCloseConn(fd)
                elif events & select.EPOLLOUT:
                    handler = self.__GetConnHandler(conn)
                    wcount = 0
                    if conn.wbuff:
                        try:
                            wcount = conn.sock.send(conn.wbuff)
                        except socket.error, msg:
                            handler.OnError(fd, msg.errno)
                            self._InnerCloseConn(fd)
                            continue
                        conn.wbuff = conn.wbuff[wcount:]

                    call_ret = False
                    try:
                        call_ret = handler.OnWrite(fd, wcount)
                    except Exception, e:
                        logger.warning(
                            "OnWrite has exp, exp=\"%s\" trace=\"%s\"", str(e),
                            traceback.format_exc())
                    if not call_ret:
                        self._InnerCloseConn(fd)
                    if not conn.wbuff:
                        self._epoll_fd.modify(fd, select.EPOLLIN |
                                              select.EPOLLERR)
                elif events & select.EPOLLERR:
                    logger.warning("Connection has an error, conn_info=%s",
                                   str(conn))
                    self._InnerCloseConn(fd)

                if conn.handler:
                    conn.handler.OnTimeout(fd)

        return True
