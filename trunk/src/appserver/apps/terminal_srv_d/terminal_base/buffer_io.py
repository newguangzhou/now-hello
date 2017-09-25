# -*- coding: utf-8 -*-
""" 
@biref simple buffer io implemet
@file buffer_io.py
@author ChenYongqiang
@date 2014-12-04
"""

try:
    import cStringIO as string_io
except:
    import StringIO as string_io


class BufferIO:
    def __init__(self, *arg, **kwargs):
        self.sio = string_io.StringIO()

    def AppendData(self, data):
        pos = self.sio.tell()
        self.sio.write(data)
        self.sio.seek(pos)

    def AppendData2(self, data):
        remain = self.sio.read()
        self.sio.truncate(0)
        self.sio.write(remain)
        self.sio.write(data)
        self.sio.seek(0)

    def GetSize(self):
        pos = self.sio.tell()
        self.sio.seek(-1, 2)
        ret = self.sio.tell()
        self.sio.seek(pos)
        if ret > 0:
            return (ret - pos) + 1
        else:
            return 0

    def Rewind(self, *args, **kwargs):
        remain = self.sio.read()
        self.sio.truncate(0)
        self.sio.write(remain)
        self.sio.seek(0)

    def GetOffset(self):
        return self.sio.tell()

    def ReadByOffset(self, offset, count):
        tmp = self.sio.tell()
        self.sio.seek(offset)
        ret = self.sio.read(count)
        self.sio.seek(tmp)
        return ret

    def ReadFully(self, count):
        pos = self.sio.tell()
        ret = self.sio.read(count)
        if len(ret) != count:
            self.sio.seek(pos)
            return None
        else:
            return ret

    def GetPos(self):
        return self.sio.tell()

    def Seek(self, offset):
        self.sio.seek(offset)

    def Read(self, count):
        return self.sio.read(count)

    def Dump(self):
        return self.sio.getvalue()
