# -*- coding: utf-8 -*-
import time
import logging
from tornado.ioloop import IOLoop
from simple_timer import SimpleTimer
logger = logging.getLogger(__name__)


class UnreplyMsgMgr:
    def __init__(self,
                 on_un_reply_msg_retry_func=None,
                 max_count=3,
                 key_expires=60):
        self.timer = SimpleTimer(self.on_exire_keys)
        self.msg_dict = {}
        self.max_count = max_count
        self.imei_msg_dict = {}
        self.on_un_reply_msg_retry_func = on_un_reply_msg_retry_func
        self.key_expires = key_expires

        if self.on_un_reply_msg_retry_func != None:
            self.timer.start()

    def set_on_un_reply_msg_retry_func(self, on_un_reply_msg_retry_func):
        self.on_un_reply_msg_retry_func = on_un_reply_msg_retry_func
        if not self.timer.is_started():
            self.timer.start()

    def add_unreply_msg(self, sn, imei, msg):
        logger.debug("add_unreply_msg sn:%s, imei:%s msg:%s", sn, imei, msg)
        seq = self.get_seq_by_sn(sn)
        msg_and_count = self.msg_dict.get((imei, seq), None)
        if msg_and_count is None:
            self.msg_dict[(imei, seq)] = [msg, self.max_count]
            seqs = self.imei_msg_dict.get(imei, None)
            if seqs is None:
                self.imei_msg_dict[imei] = set(seq)
            else:
                seqs.add(seq)

            self.timer.add_key((imei, seq), self.key_expires)
        else:
            logger.info("on add_unreply_msg imei:%s seq:%s exist", imei, seq)

    def get_seq_by_sn(self, sn):
        return sn[-4:]

    def delete_unreply_msg(self, sn, imei):
        logger.debug("delete_unreply_msg sn:%s,imei:%s ", sn, imei)

        seq = self.get_seq_by_sn(sn)
        msg_and_count = self.msg_dict.get((imei, seq), None)
        if msg_and_count is None:
            logger.warning("on delete_unreply_msg  imei:%s seq:%s not exist",
                           imei, seq)
        else:
            del self.msg_dict[(imei, seq)]
            seqs = self.imei_msg_dict.get(imei, None)
            if seqs is not None:
                try:
                    seqs.remove(seq)
                except Exception, e:
                    logger.exception(e)

    def get_un_reply_msg(self, imei):
        logger.debug("get_un_reply_msg imei:%s ", imei)
        msgs = []
        seqs = self.imei_msg_dict.get(imei, None)
        if seqs is not None:
            for sq in seqs:
                msg_and_count = self.msg_dict.get((imei, sq), None)
                if msg_and_count is not None:
                    msgs.append((sq, msg_and_count[0]))
        return msgs

    def on_exire_keys(self, keys):
        need_retry_msgs = []
        for imei, seq in keys:
            msg_and_count = self.msg_dict.get((imei, seq), None)
            if msg_and_count is None:
                logger.warning("on on_exire_keys  imei:%s seq:%s not exist",
                               imei, seq)
                continue
            msg, count = msg_and_count
            if count > 0:
                need_retry_msgs.append(
                    (seq, imei, msg_and_count[0], self.max_count - count + 1))
                msg_and_count[1] = msg_and_count[1] - 1
                self.msg_dict[(imei, seq)] = msg_and_count
            else:
                logger.warning(
                    "on on_exire_keys  imei:%s seq:%s count:%d need client reconnect",
                    imei, seq, count)
        if len(need_retry_msgs) > 0:
            self.on_un_reply_msg_retry_func(need_retry_msgs)
        for retry_msg in need_retry_msgs:
            self.timer.add_key((retry_msg[1], retry_msg[0]), self.key_expires)
