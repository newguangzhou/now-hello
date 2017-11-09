# -*- coding: utf-8 -*-
import time
import logging
from tornado.ioloop import IOLoop
from simple_timer import SimpleTimer
logger = logging.getLogger(__name__)


class UnreplyMsgMgr2:
    def __init__(self,
                 on_un_reply_msg_retry_func=None,
                 max_count=3,
                 key_expires=60):
        self.timer = SimpleTimer(self.on_exire_keys)
        self.msg_dict = {}
        self.max_count = max_count
        self.imei_seq = {}
        self.on_un_reply_msg_retry_func = on_un_reply_msg_retry_func
        self.key_expires = key_expires

        if self.on_un_reply_msg_retry_func != None:
            self.timer.start()

    def set_on_un_reply_msg_retry_func(self, on_un_reply_msg_retry_func):
        self.on_un_reply_msg_retry_func = on_un_reply_msg_retry_func
        if not self.timer.is_started():
            self.timer.start()

    def add_unreply_msg(self, sn, imei, msg, msg_type):
        logger.debug("add_unreply_msg sn:%s, imei:%s msg:%s msg_type:%s", sn,
                     imei, msg, msg_type)
        seq = self.get_seq_by_sn(sn)
        #msg_and_count = self.msg_dict.get((imei, msg_type), None)
        self.msg_dict[(imei, msg_type)] = [msg, self.max_count, seq]
        sub_imei_seq = self.imei_seq.get(imei, None)
        if sub_imei_seq is None:
            sub_imei_seq = {seq: msg_type}
        else:
            sub_imei_seq[seq] = msg_type
        self.imei_seq[imei] = sub_imei_seq
        self.timer.add_key((imei, seq), self.key_expires)

    def get_seq_by_sn(self, sn):
        return sn[-4:]

    def delete_unreply_msg(self, sn, imei):
        logger.debug("delete_unreply_msg sn:%s,imei:%s ", sn, imei)

        seq = self.get_seq_by_sn(sn)
        msg_and_count, msg_type = self._get_msg_and_count_by_seq(imei, seq)
        if msg_and_count is not None:
            if msg_and_count[2] == seq:
                logger.info("delete_unreply_msg seq:%s imei:%s find ", seq,
                            imei)
                del self.msg_dict[(imei, msg_type)]
            else:
                logger.warning(
                    "delete_unreply_msg seq:%s imei:%s not find may be removed",
                    seq, imei)
            del self.imei_seq[imei][seq]

    def get_un_reply_msg(self, imei):
        logger.debug("get_un_reply_msg imei:%s ", imei)

        msgs = []

        sub_imei_seq = self.imei_seq.get(imei, None)
        if sub_imei_seq is not None:
            msg_types = sub_imei_seq.values()
            msg_types = set(msg_types)
            for msg_type in msg_types:
                msg_and_count = self.msg_dict.get((imei, msg_type), None)
                if msg_and_count is not None:
                    msgs.append((msg_and_count[2], msg_and_count[0]))
                    #del self.msg_dict[(imei, msg_type)]

        return msgs

    def _get_msg_and_count_by_seq(self, imei, seq):
        logger.debug("_get_msg_and_count_by_seq imei:%s seq:%s", imei, seq)
        msg_count = None
        msg_type = None
        sub_imei_seq = self.imei_seq.get(imei, None)
        if sub_imei_seq is not None:
            msg_type = sub_imei_seq.get(seq, None)
            if msg_type is not None:
                msg_count = self.msg_dict.get((imei, msg_type), None)
        return msg_count, msg_type

    def on_exire_keys(self, keys):
        need_retry_msgs = []
        for imei, seq in keys:
            msg_and_count, msg_type = self._get_msg_and_count_by_seq(imei, seq)
            if msg_and_count is None:
                logger.warning("on on_exire_keys  imei:%s seq:%s not exist",
                               imei, seq)
                continue
            if msg_and_count[2] == seq:
                if msg_and_count[1] > 0:
                    need_retry_msgs.append(
                        (seq, imei, msg_and_count[0],
                         self.max_count - msg_and_count[1] + 1))
                    msg_and_count[1] = msg_and_count[1] - 1
                    self.msg_dict[(imei, msg_type)] = msg_and_count
                else:
                    logger.warning(
                        "on on_exire_keys  imei:%s seq:%s count:%d need client reconnect",
                        imei, seq, msg_and_count[1])
            else:
                logger.warning(
                    "on on_exire_keys imei:%s seq:%s not eq seq:%s may be replaced",
                    imei, seq, msg_and_count[2])
        if len(need_retry_msgs) > 0:
            self.on_un_reply_msg_retry_func(need_retry_msgs)
        for retry_msg in need_retry_msgs:
            self.timer.add_key((retry_msg[1], retry_msg[0]), self.key_expires)
