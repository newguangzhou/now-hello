# -*- coding: utf-8 -*-

import pdb

import terminal_proto
import logging
from util import change_unescape_ssid


class PacketException(Exception):
    def __init__(self, message, *args):
        self._msg = message % tuple(args)

    def __str__(self):
        return self._msg


"""
定位状态
"""
LOCATOR_STATUS_GPS = 0  # GPS定位成功
LOCATOR_STATUS_FAILED = 1  # 定位失败
LOCATOR_STATUS_STATION = 2  # 基站地位
#LOCATOR_STATUS_WIFI = 3  # WIFI定位
LOCATOR_STATUS_MIXED = 5  # 混合定位
"""
位置信息
"""


class LocationInfo(terminal_proto.ComplexField):
    def __init__(self, *args, **kwargs):
        terminal_proto.ComplexField.__init__(self, *args, **kwargs)
        self._data = ""

    def Parse(self, data):
        # 获取定位状态
        self._data = data
        self.fields["locator_status"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(data[0:1])
        #print data
        #print self.locator_status
        # 获取定位数据
        if self.locator_status == LOCATOR_STATUS_GPS:  # GPS
            # 获取经度类型(E or W)
            self.fields["longitude_type"] = terminal_proto.Field(
                terminal_proto.STRING_FIELD).FromStr(data[1:2])

            # 获取经度
            self.fields["longitude"] = terminal_proto.Field(
                terminal_proto.FLOAT_FIELD).FromStr(data[2:12])

            # 获取维度类型(N or S)
            self.fields["latitude_type"] = terminal_proto.Field(
                terminal_proto.STRING_FIELD).FromStr(data[12:13])

            # 获取维度
            self.fields["latitude"] = terminal_proto.Field(
                terminal_proto.FLOAT_FIELD).FromStr(data[13:22])
            print data[23:37]
            # 获取定位时间
            self.fields["locator_time"] = terminal_proto.Field(
                terminal_proto.DATE_FIELD).FromStr(data[23:37])
        elif self.locator_status == LOCATOR_STATUS_STATION or self.locator_status == LOCATOR_STATUS_MIXED:  # 获取基站或者混合定位数据
            n = len(data) - 15
            if n <= 0:
                raise PacketException("Invalid location info")

            #f = terminal_proto.Field(terminal_proto.STRING_FIELD).FromStr(data[
            #    1:n + 1])
            tmp = data[1:n]
            if self.locator_status == LOCATOR_STATUS_MIXED:
                pos = tmp.find("%")
                if pos == 0:
                    raise PacketException("Invalid location  mixed info")
                segs5 = [tmp[0:pos], tmp[pos + 1:]]
                #logging.info("tang seqs5 pos:%d#####%s#####%s" %
                #             (pos, segs5, tmp))
                self.fields["station_locator_data"] = terminal_proto.Field(
                    terminal_proto.STRING_FIELD).FromStr(segs5[0])
                self.fields["mac"] = terminal_proto.Field(
                    terminal_proto.STRING_FIELD).FromStr(change_unescape_ssid(
                        segs5[1]))
            else:
                self.fields["station_locator_data"] = terminal_proto.Field(
                    terminal_proto.STRING_FIELD).FromStr(tmp)
            self.fields["locator_time"] = terminal_proto.Field(
                terminal_proto.DATE_FIELD).FromStr(data[n + 1:14 + n + 1])
        elif self.locator_status == LOCATOR_STATUS_FAILED:
            self.fields["locator_time"] = terminal_proto.Field(
                terminal_proto.DATE_FIELD).FromStr(data[2:16])
        else:
            raise PacketException("Invalid location info")

    def __str__(self):
        ret = ""
        ret += str(self.locator_status)

        if self.locator_status == LOCATOR_STATUS_GPS:
            ret += str(self.longitude_type)
            ret += str(self.longitude)
            ret += str(self.latitude_type)
            ret += str(self.latitude)
        elif self.locator_status == LOCATOR_STATUS_STATION:
            ret += str(self.station_locator_data)
        elif self.locator_status == LOCATOR_STATUS_MIXED:
            ret += str(self.station_locator_data)
            ret += str(self.mac)

        ret += "T" + str(self.locator_time)

        return ret

    def orgin_data(self):
        return self._data


"""
上传位置报文定义
"""


class ReportLocationInfoReq:
    def __init__(self, *args, **kwargs):
        self._fields = {}
        self._data = ""

    def Parse(self, data):
        self._data = data
        pos = data.find("@")
        if pos == 0:
            raise PacketException(
                "Invalid report location info request packet")
        segs = [data[0:pos], data[pos + 1:]]
        # 获取imei
        self._fields["imei"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[0])

        # 得到参数和附加参数列表
        pos = segs[1].rfind("#")
        if pos == 0:
            raise PacketException(
                "Invalid report location info request packet")
        segs3 = [segs[1][0:pos], segs[1][pos + 1:]]
        # 获取定位状态
        self._fields["locator_status"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs3[0][0:1])

        # 获取定位数据
        locatorInfo = LocationInfo()
        locatorInfo.Parse(segs3[0])
        self._fields["location_info"] = locatorInfo

        # 获取附加数据
        segs4 = segs3[1].split(",")
        if len(segs4) != 5:
            raise PacketException(
                "Invalid report location info request packet")

        self._fields["status"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs4[0])  # 状态
        self._fields["electric_quantity"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs4[1])  # 电量
        self._fields["step_count"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs4[2])  # 步数
        self._fields["distance"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs4[3])  # 距离
        self._fields["calorie"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs4[4])  # 卡路里

    def __getattr__(self, attr):
        if self._fields.has_key(attr):
            return self._fields[attr].Value()
        else:
            raise PacketException("\"%s\" attribute not exists" % (attr, ))

    def __str__(self):
        return terminal_proto.FieldsStr(self._fields)

    def orgin_data(self):
        return self._data


class ReportLocationInfoAck:
    def __init__(self, *args, **kwargs):
        self.sn = None
        if len(args) > 0:
            self.sn = terminal_proto.GenReturnSn(args[0])
        else:
            self.sn = terminal_proto.GenReturnSn(kwargs["sn"])

    def __str__(self):
        ret = "[%s,R01,1,0]" % (self.sn, )
        return ret

    def orgin_data(self):
        return self.__str__()


"""
上传睡眠心率报文定义
"""


class ReportHealthInfoReq:
    def __init__(self, *args, **kwargs):
        self._fields = {}
        self._data = ""

    def Parse(self, data):
        #pdb.set_trace()
        self._data = data
        segs = data.split("@")
        if len(segs) != 2:
            raise PacketException("Invalid report health info request packet")

        # 获取imei
        self._fields["imei"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[0])

        # 得到健康信息
        segs3 = segs[1].split("#")
        if len(segs3) <= 0:
            raise PacketException("Invalid report health info request packet")
        for v in segs3:
            # 得到健康数据段类型
            tp = terminal_proto.Field(terminal_proto.INTEGER_FIELD).FromStr(v[
                0:1]).Value()

            # 得到健康数据
            if tp == 1:  # 睡眠数据
                tmp = terminal_proto.ComplexField()

                segs4 = v[2:].split(",")
                if len(segs4) != 3:
                    raise PacketException(
                        "Invalid report health info request packet")

                tmp.fields["begin_time"] = terminal_proto.Field(
                    terminal_proto.DATE_FIELD).FromStr(segs4[0])  # 开始时间

                #  得到总时间以秒位单位
                totalTimeStr = segs4[1]
                tmp.fields["total_secs"] = terminal_proto.Field(
                    terminal_proto.INTEGER_FIELD).FromStr(totalTimeStr)

                tmp.fields["quality"] = terminal_proto.Field(
                    terminal_proto.INTEGER_FIELD).FromStr(segs4[2])  # 睡眠质量

                if not self._fields.has_key("sleep_data"):
                    self._fields["sleep_data"] = []
                self._fields["sleep_data"].append(tmp)
            elif tp == 2:  # 心率数据
                tmp = terminal_proto.ComplexField()

                tmp.fields["begin_time"] = terminal_proto.Field(
                    terminal_proto.DATE_FIELD).FromStr(v[2:16])  # 开始时间
                tmp.fields["value"] = terminal_proto.Field(
                    terminal_proto.INTEGER_FIELD).FromStr(v[17:])

                if not self._fields.has_key("heart_rate_data"):
                    self._fields["heart_rate_data"] = []
                self._fields["heart_rate_data"].append(tmp)
            else:
                raise PacketException(
                    "Invalid report health info request packet")

    def __getattr__(self, attr):
        tmp = self._fields.get(attr, None)
        if tmp is not None:
            if type(tmp) == list:
                return tmp
            else:
                return tmp.Value()
        else:
            raise PacketException("\"%s\" attribute not exists" % (attr, ))

    def __str__(self):
        return terminal_proto.FieldsStr(self._fields)

    def orgin_data(self):
        return self._data


class ReportHealthInfoAck:
    def __init__(self, *args, **kwargs):
        self.sn = None
        if len(args) > 0:
            self.sn = terminal_proto.GenReturnSn(args[0])
        else:
            self.sn = terminal_proto.GenReturnSn(kwargs["sn"])

    def __str__(self):
        ret = "[%s,R02,1,0]" % (self.sn, )
        return ret

    def orgin_data(self):
        return self.__str__()


"""
同步指令
"""


class SyncCommandReq:
    def __init__(self, *args, **kwargs):
        self._data = ""
        self._fields = {}

    def Parse(self, data):
        #pdb.set_trace()
        self._data = data
        segs = data.split("@")
        if len(segs) != 2:
            raise PacketException("Invalid report health info request packet")

        # 获取imei
        self._fields["imei"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[0])
        self._fields["command"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[1])

    def __getattr__(self, attr):
        if self._fields.has_key(attr):
            return self._fields[attr].Value()
        else:
            raise PacketException("\"%s\" attribute not exists" % (attr, ))

    def __str__(self):
        return terminal_proto.FieldsStr(self._fields)

    def orgin_data(self):
        return self._data


class SyncCommandResp:
    def __init__(self, *args, **kwargs):
        self.sn = None
        self.imei = None  # IMEI号
        self.command_pk = None  # 指令
        self.result = 0  # 结果，0为成功，1为失败
        if len(args) > 0:
            self.sn = terminal_proto.GenReturnSn(args[0])
        else:
            self.sn = terminal_proto.GenReturnSn(kwargs["sn"])

        if len(args) > 1:
            self.command_pk = args[1]
        else:
            self.command_pk = kwargs["command_pk"]

        if len(args) > 2:
            self.result = args[2]
        elif kwargs.has_key("result"):
            self.result = kwargs["result"]

    def __str__(self):
        body = "%d@%s" % (self.result, str(self.command_pk))

        return "[%s,R04,%d,%s]" % (terminal_proto.GenSN(), len(body), body)

    def orgin_data(self):
        return self.__str__()


"""
远程设置参数报文定义
"""


class SendCommandReq:
    def __init__(self, *args, **kwargs):
        self.imei = None  # IMEI号
        self.command_pk = None  # 指令
        self.sn = terminal_proto.GenSN()

        if len(args) > 0:
            self.imei = args[0]
        else:
            self.imei = kwargs["imei"]

        if len(args) > 1:
            self.command_pk = args[1]
        else:
            self.command_pk = kwargs["command_pk"]

    def __str__(self):
        body = "%s@%s" % (self.imei, self.command_pk)

        return "[%s,J03,%d,%s]" % (self.sn, len(body), body)

    def orgin_data(self):
        return self.__str__()


class SendCommandAck:
    def __init__(self, *args, **kwargs):
        self._fields = {}
        self._data = ""

    def Parse(self, data):
        self._data = data
        segs = data.split("@")
        if len(segs) != 2:
            raise PacketException("Invalid set params ack packet")

        # 获取imei
        self._fields["imei"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[0])

        # 获取指令名
        self._fields["command"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[1])

    def __getattr__(self, attr):
        if self._fields.has_key(attr):
            return self._fields[attr].Value()
        else:
            raise PacketException("\"%s\" attribute not exists" % (attr, ))

    def __str__(self):
        return terminal_proto.FieldsStr(self._fields)

    def orgin_data(self):
        return self._data


"""
心跳
"""


class HeatbeatReq:
    def __init__(self, *args, **kwargs):
        self._fields = {}
        self._data = ""

    def Parse(self, data):
        self._data = data
        segs = data.split("@")
        if len(segs) != 2:
            raise PacketException("Invalid heatbeat req packet")

        # 获取imei
        self._fields["imei"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[0])

        if segs[1] != "Heart":
            raise PacketException("Invalid heatbeat req packet")

    def __getattr__(self, attr):
        if self._fields.has_key(attr):
            return self._fields[attr].Value()
        else:
            raise PacketException("\"%s\" attribute not exists" % (attr, ))

    def __str__(self):
        return terminal_proto.FieldsStr(self._fields)

    def orgin_data(self):
        return self._data


class HeatbeatAck:
    def __init__(self, *args, **kwargs):
        self.sn = None  # 流水号

        if len(args) > 0:
            self.sn = terminal_proto.GenReturnSn(args[0])
        else:
            self.sn = terminal_proto.GenReturnSn(kwargs["sn"])

    def __str__(self):
        return "[%s,R12,5,Heart]" % (self.sn, )

    def orgin_data(self):
        return self.__str__()


"""
上传设备状态数据
"""


class ReportTerminalStatusReq:
    def __init__(self, *args, **kwargs):
        self._fields = {}
        self._data = ""

    def Parse(self, data):
        self._data = data
        segs = data.split("@")
        if len(segs) != 2:
            raise PacketException("Invalid report terminal status req packet")

        # 获取imei
        self._fields["imei"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[0])

        # 获取状态数据
        segs3 = segs[1].split("%")
        if len(segs3) != 4:
            raise PacketException("Invalid report terminal status req packet")

        self._fields["iccid"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs3[0])  # SIM卡卡号
        self._fields["hardware_version"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs3[1])  # 硬件版本
        self._fields["software_version"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs3[2])  # 软件版本
        self._fields["electric_quantity"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs3[3])  # 电量

    def __getattr__(self, attr):
        if self._fields.has_key(attr):
            return self._fields[attr].Value()
        else:
            raise PacketException("\"%s\" attribute not exists" % (attr, ))

    def __str__(self):
        return terminal_proto.FieldsStr(self._fields)

    def orgin_data(self):
        return self._data


class ReportTerminalStatusAck:
    def __init__(self, *args, **kwargs):
        self.sn = None  # 流水号
        self.result = 0  # 结果，0为成功，1为失败

        if len(args) > 0:
            self.sn = terminal_proto.GenReturnSn(args[0])
        else:
            self.sn = terminal_proto.GenReturnSn(kwargs["sn"])

        if len(args) > 1:
            self.result = args[1]
        elif kwargs.has_key("result"):
            self.result = kwargs["result"]

    def __str__(self):
        return "[%s,R17,1,%d]" % (self.sn, self.result)

    def orgin_data(self):
        return self.__str__()


"""
上传设备日志数据
"""


class UploadTerminalLogReq:
    def __init__(self, *args, **kwargs):
        self._fields = {}
        self._data = ""

    def Parse(self, data):
        self._data = data
        segs = data.split("@")
        if len(segs) != 2:
            raise PacketException("Invalid upload terminal log req packet")

        # 获取imei
        self._fields["imei"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[0])

        # 获取日志数据
        segs3 = segs[1].split("%")
        if len(segs3) <= 0:
            raise PacketException("Invalid upload terminal log req packet")
        for v in segs3:
            segs4 = v.split(",")
            if len(segs4) != 2:
                raise PacketException("Invalid upload terminal log req packet")

            f = terminal_proto.ComplexField()
            f.fields["time"] = terminal_proto.Field(
                terminal_proto.DATE_FIELD).FromStr(segs4[0])  # 日志时间
            f.fields["type"] = terminal_proto.Field(
                terminal_proto.INTEGER_FIELD).FromStr(segs4[1])  # 日志类型

            if not self._fields.has_key("log_items"):
                self._fields["log_items"] = []
            self._fields["log_items"].append(f)

    def __getattr__(self, attr):
        tmp = self._fields.get(attr, None)
        if tmp is not None:
            if type(tmp) == list:
                return tmp
            else:
                return tmp.Value()
        else:
            raise PacketException("\"%s\" attribute not exists" % (attr, ))

    def __str__(self):
        return terminal_proto.FieldsStr(self._fields)

    def orgin_data(self):
        return self._data


class UploadTerminalLogAck:
    def __init__(self, *args, **kwargs):
        self.sn = None  # 流水号
        self.result = 0  # 结果，0为成功，1为失败

        if len(args) > 0:
            self.sn = terminal_proto.GenReturnSn(args[0])
        else:
            self.sn = terminal_proto.GenReturnSn(kwargs["sn"])

        if len(args) > 1:
            self.result = args[1]
        elif kwargs.has_key("result"):
            self.result = kwargs["result"]

    def __str__(self):
        return "[%s,R18,1,%d]" % (self.sn, self.result)

    def orgin_data(self):
        return self.__str__()


#gps开关确认
class GPSSwtichReq:
    def __init__(self, *args, **kwargs):
        self._fields = {}
        self._data = ""

    def Parse(self, data):
        self._data = data
        segs = data.split("@")
        if len(segs) != 2:
            raise PacketException("Invalid upload station log req packet")

        # 获取imei
        self._fields["imei"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[0])

        segs2 = segs[1][1:].split("#")
        if len(segs2) != 2:
            raise PacketException("Invalid upload station log req packet")

        segs3 = segs2[0].split(";")
        if len(segs3) != 2:
            raise PacketException("Invalid upload station log req packet")

        self._fields["station_locator_data"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs3[0])

        self._fields["near_station_locator_data"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs3[1])

        # 获取附加数据
        segs4 = segs2[1].split(",")
        if len(segs4) != 5:
            raise PacketException(
                "Invalid report location info request packet")

        self._fields["status"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs4[0])  # 状态
        self._fields["electric_quantity"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs4[1])  # 电量
        self._fields["step_count"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs4[2])  # 步数
        self._fields["distance"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs4[3])  # 距离
        self._fields["calorie"] = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs4[4])  # 卡路里

    def __getattr__(self, attr):
        tmp = self._fields.get(attr, None)
        if tmp is not None:
            if type(tmp) == list:
                return tmp
            else:
                return tmp.Value()
        else:
            raise PacketException("\"%s\" attribute not exists" % (attr, ))

    def __str__(self):
        return terminal_proto.FieldsStr(self._fields)

    def orgin_data(self):
        return self._data


class GPSSwtichAck:
    def __init__(self, *args, **kwargs):
        self.sn = None  # 流水号
        self.result = 0  # 结果，0为成功，1为失败

        if len(args) > 0:
            self.sn = terminal_proto.GenReturnSn(args[0])
        else:
            self.sn = terminal_proto.GenReturnSn(kwargs["sn"])

        if len(args) > 1:
            self.result = args[1]
        elif kwargs.has_key("result"):
            self.result = kwargs["result"]

    def __str__(self):
        return "[%s,R15,1,%d]" % (self.sn, self.result)

    def orgin_data(self):
        return self.__str__()


class UploadStationReq:
    def __init__(self, *args, **kwargs):
        self._fields = {}
        self._data = ""

    def Parse(self, data):
        self._data = data
        segs = data.split("@")
        if len(segs) != 2:
            raise PacketException("Invalid upload station log req packet")

        # 获取imei
        self._fields["imei"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[0])

        self._fields["station_locator_data"] = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[1][1:])

    def __getattr__(self, attr):
        tmp = self._fields.get(attr, None)
        if tmp is not None:
            if type(tmp) == list:
                return tmp
            else:
                return tmp.Value()
        else:
            raise PacketException("\"%s\" attribute not exists" % (attr, ))

    def __str__(self):
        return terminal_proto.FieldsStr(self._fields)

    def orgin_data(self):
        return self._data


#上传基站数据ack
class UploadStationAck:
    def __init__(self, *args, **kwargs):
        self.sn = None  # 流水号
        self.lng = float(0)  # 结果，0为成功，1为失败
        self.lat = float(0)

        if len(args) > 0:
            self.sn = terminal_proto.GenReturnSn(args[0])
        else:
            self.sn = terminal_proto.GenReturnSn(kwargs["sn"])

        if len(args) > 1:
            self.lng = args[1]
        else:
            self.lng = kwargs["lng"]

        if len(args) > 2:
            self.lat = args[2]
        else:
            self.lat = kwargs["lat"]

    def __str__(self):
        if self.lng > float(0):
            str_lng = "E%.6f" % self.lng
        else:
            str_lng = "W%.6f" % -self.lng

        if self.lat > float(0):
            str_lat = "N%.6f" % self.lat
        else:
            str_lat = "S%.6f" % -self.lat

        body = "%s%s" % (str_lng, str_lat)
        return "[%s,R16,%d,%s]" % (self.sn, len(body), body)

    def orgin_data(self):
        return self.__str__()


class GetLocationAck:
    def __init__(self, *args, **kwargs):
        self.sn = None  # 流水号
        self.imei = ""
        if len(args) > 0:
            self.sn = terminal_proto.GenReturnSn(args[0])
        else:
            self.sn = terminal_proto.GenReturnSn(kwargs["sn"])
        if len(args) > 1:
            self.imei = args[1]
        else:
            self.imei = kwargs["imei"]

    def __str__(self):
        return "[%s,J13,%d,%s@Location]" % (self.sn, len(self.imei) + 9,
                                            self.imei)

    def orgin_data(self):
        return self.__str__()


def main():
    #msg = UploadStationReq()
    #msg.Parse(
    #    "123456789012345@0460,01,40977,2205409,-65|460,01,40977 ,2205409,-65|460,01,40977,2205409,-65")
    #print msg
    #msg = UploadStationAck("200710231200001000", 121.411783, 31.178125)
    #print msg
    test_str = "5460,0,9470,22175,36|460,0,9470,22927,44|460,0,9470,23408,42|460,0,9470,48805,38|460,0,9470,22928,37|460,0,9470,23107,32|460,0,9470,55443,30%B8:08:D7:5B:6E:EC,-67,XMQ_WIFI|64:09:80:5A:95:69,-61,XMQ_WIFI|EC:26:CA:40:8F:AA,-77,TP-LINK_sengnon|30:B4:9E:29:22:B0,-90,Eco-Mobile|CC:81:DA:8A:F9:08,-95,@PHICOMM_00|T20170522195311#00,100,13,11,69"
    pos = test_str.rfind("#")
    if pos == 0:
        print "err"
    seq = [test_str[0:pos], test_str[pos + 1:]]
    print seq


if __name__ == '__main__':
    main()