# -*- coding: utf-8 -*-

import buffer_io
import datetime
import time
import pdb
from tornado import gen
from tornado.locks import Lock
INTEGER_FIELD = 1
STRING_FIELD = 2
DATE_FIELD = 3
FLOAT_FIELD = 4
import logging
SIMPLE_HEART = "[]"
ERROR_START=-1
_field_tps = set([INTEGER_FIELD, STRING_FIELD, DATE_FIELD, FLOAT_FIELD])


class ProtoException(Exception):
    def __init__(self, message, *args):
        self._msg = message % tuple(args)

    def __str__(self):
        return self._msg


_packet_seqnum = 0
"""
字段定义
"""


class Field:
    def __init__(self, *args, **kwargs):
        self._tp = 0
        if len(args) > 0:
            self._tp = args[0]
        else:
            self._tp = kwargs["tp"]

        if self._tp not in _field_tps:
            raise ProtoException("Invalid terminal packet field tp, tp=%d",
                                 self._tp)

        self._value = None
        if len(args) > 1:
            self._value = args[1]
        elif kwargs.has_key("value"):
            self._value = kwargs["value"]
        if self._value:
            self._check_value(self._value)

    def _check_value(self, val):
        result = False
        if self._tp == INTEGER_FIELD:
            result = isinstance(val, int)
        elif self._tp == STRING_FIELD:
            result = isinstance(val, str)
        elif self._tp == DATE_FIELD:
            result = isinstance(val, datetime.datetime)
        elif self._tp == FLOAT_FIELD:
            result = isinstance(val, float)

        if not result:
            raise ProtoException(
                "Invalid termial packet field value, tp must be %d", self._tp)

    def __str__(self):
        if self._value is None:
            raise ProtoException("Terminal packet field value not set, tp=%d",
                                 self._tp)

        if self._tp == INTEGER_FIELD:
            return str(self._value)
        elif self._tp == STRING_FIELD:
            return self._value
        elif self._tp == DATE_FIELD:
            return "%02d%02d%02d%02d%02d%02d" % (
                self._value.year, self._value.month, self._value.day,
                self._value.hour, self._value.minute, self._value.second)
        elif self._tp == FLOAT_FIELD:
            return "%.6f" % (self._value, )

    """
    将指定的字符串转换成field的value
    """

    def FromStr(self, v):
        if self._tp == INTEGER_FIELD:
            self._value = int(v)
        elif self._tp == STRING_FIELD:
            self._value = str(v)
        elif self._tp == DATE_FIELD:
            self._value = datetime.datetime.fromtimestamp(time.mktime(
                time.strptime(v, "%Y%m%d%H%M%S")))
        elif self._tp == FLOAT_FIELD:
            self._value = float(v)

        return self

    def Value(self):
        return self._value


def FieldDict(fields):
    ret = {}
    for k, v in fields.items():
        ret[k] = v.Value()
    return ret


def FieldsStr(fields):
    ret = "{"
    i = 0
    for k, v in fields.items():
        ret += k + ":" + str(v)
        if i != len(fields) - 1:
            ret += ","
        i += 1
    ret += "}"
    return ret


"""
复合字段定义
"""


class ComplexField:
    def __init__(self, *args, **kwargs):
        self.fields = {}

    def __getattr__(self, attr):
        if self.fields.has_key(attr):
            return self.fields[attr].Value()
        else:
            raise ProtoException("\"%s\" attribute not exists" % (attr, ))

    def __str__(self):
        return FieldsStr(self.fields)

    def __repr__(self):
        return FieldsStr(self.fields)

    def Value(self):
        return self


"""
生成sn
"""


def GenSN():
    global _packet_seqnum

    if _packet_seqnum > 9999:
        _packet_seqnum = 0

    _packet_seqnum += 1
    return _gen_sn(_packet_seqnum)


def _gen_sn(seq):
    dt = datetime.datetime.now()
    sn = "%02d%02d%02d%02d%02d%02d%04d" % (dt.year, dt.month, dt.day, dt.hour,
                                           dt.minute, dt.second, seq)
    return sn


def GetSeqBySn(sn):
    return int(sn[-4:])


def GenReturnSn(sn):
    return _gen_sn(GetSeqBySn(sn))


class Header:
    def __init__(self):
        self.sn = None
        self.directive = None
        self.content_length = None

    def __str__(self):
        return "sn:%s,directive:%s,content_length:%d" % (
            self.sn, self.directive, self.content_length)


"""
协议IO定义
"""


class ProtoIO:
    def __init__(self, *args, **kwargs):
        self.read_buff = buffer_io.BufferIO()

    """
    读取一个报文, 报文以‘[’开始以']'结尾
    """

    def Read(self):
        #pdb.set_trace()

        pos = self.read_buff.GetPos()

        # Read header
        header = self._ReadHeader()
        if header == ERROR_START:
            return (ERROR_START,None)
        if header == SIMPLE_HEART:
            return (header, None)

        if header is None:
            return (None, None)
        # Read body
        body = None
        if self.read_buff.GetSize() >= header.content_length + 1:
            body = self.read_buff.Read(header.content_length)
            end_tag = self.read_buff.Read(1)
            if end_tag != "]":
                raise ProtoException("Invalid terminal packet in Read")
        if body is None:
            self.read_buff.Seek(pos)
            header = None

        return (header, body)

    """
    得到报文头信息, 返回值为 (流水号, 指令名)
    """

    def _ReadHeader(self):
        # pdb.set_trace()

        pos = self.read_buff.GetPos()
        pkData = self.read_buff.Read(40)
        if len(pkData) < 2:
            self.read_buff.Seek(pos)
            return None

        if pkData[0] != "[":
            # raise ProtoException("Invalid terminal packet:%s" % (pkData))
            self.read_buff.Seek(pos + 1)
            return ERROR_START
        if pkData[1] == "]":
            self.read_buff.Seek(pos + 2)
            return SIMPLE_HEART

        if len(pkData) < 25:
            self.read_buff.Seek(pos)
            return None

        sn = pkData[1:19]
        directive = pkData[20:23]

        i = -1
        tmp = ""
        if len(pkData) - 24 > 10:
            tmp = pkData[24:34]
        else:
            tmp = pkData[24:]
        i = tmp.find(",")
        if i < 0:
            self.read_buff.Seek(pos)
            return None

        content_length = int(tmp[:i])

        self.read_buff.Seek(pos + 24 + i + 1)

        ret = Header()
        ret.sn = sn
        ret.directive = directive
        ret.content_length = content_length

        return ret


class ProtoIoGuarder:
    def __init__(self, proto_io):
        self.lock = Lock()
        self.proto_io = proto_io

    @gen.coroutine
    def get(self):
        yield self.lock.acquire()
        raise gen.Return(self.proto_io)

    def release(self):
        self.lock.release()
