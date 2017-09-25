# -*- coding: utf-8 -*-

import terminal_proto


class CommandException(Exception):
    def __init__(self, message, *args):
        self._msg = message % tuple(args)

    def __str__(self):
        return self._msg


class Params:
    def __init__(self, *args, **kwargs):
        self.report_time = 0  # 分时段上报间隔，以分钟位单位最大值为60
        self.add_friend = 0
        self.step_enable = 0
        self.profile = 0
        self.love = 0
        self.remote_alert = ''
        self.low_power = 0
        self.sos = 0
        self.take_off = 0
        self.gps_enable = 0
        self.step_target = 5000
        self._data = ""

    def Parse(self, data):
        self._data = ""
        segs = data.split(",")
        if len(segs) != 11 or segs[0] != "005":
            raise CommandException("Invalid params command")

        self.report_time = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs[0]).Value()
        self.add_friend = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs[1]).Value()
        self.step_enable = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs[2]).Value()
        self.profile = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs[3]).Value()
        self.love = terminal_proto.Field(terminal_proto.INTEGER_FIELD).FromStr(
            segs[4]).Value()
        self.remote_alert = terminal_proto.Field(
            terminal_proto.STRING_FIELD).FromStr(segs[5]).Value()
        self.low_power = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs[6]).Value()
        self.sos = terminal_proto.Field(terminal_proto.INTEGER_FIELD).FromStr(
            segs[7]).Value()
        self.take_off = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs[8]).Value()
        self.gps_enable = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs[9]).Value()
        self.step_target = terminal_proto.Field(
            terminal_proto.INTEGER_FIELD).FromStr(segs[10]).Value()

    def __str__(self):
        return "005,%d#%d#%d#%d#%d#%s#%d#%d#%d#%d#%d" % (
            self.report_time, self.add_friend, self.step_enable, self.profile,
            self.love, self.remote_alert, self.low_power, self.sos,
            self.take_off, self.gps_enable, self.step_target)

    def orgin_data(self):
        return self._data


class Find:
    def __str__(self):
        return "006"

    def orgin_data(self):
        return self.__str__()


class RemotePowerOff:
    def __init__(self, *args, **kwargs):
        pass

    def Parse(self, data):
        if data != "007":
            raise CommandException("Invalid remote power off command")

    def __str__(self):
        return "007"

    def orgin_data(self):
        return self.__str__()


class TermimalReset:
    def __str__(self):
        return "015"

    def orgin_data(self):
        return self.__str__()


#传参数格式
class UploadInterval:
    def __init__(self, *args):
        #self.report_time = 0  # 分时段上报间隔，以分钟位单位最大值为60
        self.intervals = []
        len_arg = len(args)
        if len_arg > 0:
            self.intervals = args

    def __str__(self):
        interval = ""
        for index, tmp in enumerate(self.intervals):
            interval += "%s#%s#%s#%d" % (tmp[0], tmp[1], tmp[2], tmp[3])
            if index != len(self.intervals) - 1:
                interval += "%"
        return "012,%s" % (interval)

    def orgin_data(self):
        return self.__str__()


class StepInterVal:
    def __init__(self, *args):
        self.status = 0  #计步器开关，0:关闭，1:一直开， 2 分时段开
        self.intervals = []
        len_arg = len(args)
        if len_arg > 0:
            self.status = args[0]
        for i in range(1, len_arg):
            self.intervals.append(args[i])

    def __str__(self):
        if self.status in (0, 1):
            return "013,%d" % self.status
        else:
            interval = ""
            for index, tmp in enumerate(self.intervals):
                interval += "%s#%s" % (tmp[0], tmp[1])
                if index != len(self.intervals) - 1:
                    interval += "%"
            return "013,%d%%%s" % (self.status, interval)

    def orgin_data(self):
        return self.__str__()


class PetLocation:
    def __init__(self):
        self.battery_threshold = 0
        self.history_location_switch = 0
        self.light_flash = []
        self.pet_weight = "0"
        self.pet_gender = 1

    def __str__(self):
        light_flash_str = ""
        for index, tmp in enumerate(self.light_flash):
            light_flash_str += "%d,%d" % (tmp[0], tmp[1])
            if index != len(self.light_flash) - 1:
                light_flash_str += "#"
        return "017,%d%%%d%%%s%%%s%%%d" % (
            self.battery_threshold, self.history_location_switch,
            light_flash_str, self.pet_weight, self.pet_gender)

    def orgin_data(self):
        return self.__str__()


class ServerConfig:
    def __init__(self):
        self.server_ip = ""
        self.server_port = 5050

    def __str__(self):
        return "019,A%%%s%%%d" % (self.server_ip, self.server_port)

    def orgin_data(self):
        return self.__str__()


class TermimalReboot:
    def __str__(self):
        return "020"

    def orgin_data(self):
        return self.__str__()


def main():

    #print "013"
    msg = StepInterVal(2, ("0900", "1100"), ("1200", "1400"))
    print msg

    msg = UploadInterval(("0900", "1100", "1111111", 2),
                         ("1100", "1200", "1111111", 4))
    #print "012"
    print msg

    msg = PetLocation()
    msg.battery_threshold = 20
    msg.history_location_switch = 0
    msg.light_flash = [(1, 5), (1, 7)]
    msg.pet_weight = "15.2"
    msg.pet_gender = 1
    msg.server_ip = "127.0.0.1"
    msg.server_port = 5050
    #print 017
    #print msg

    msg = Params()
    msg.report_time = 10  # 分时段上报间隔，以分钟位单位最大值为60
    msg.add_friend = 0
    msg.step_enable = 0
    msg.profile = 1
    msg.love = 0
    msg.remote_alert = "18222122212"
    msg.low_power = 0
    msg.sos = 0
    msg.take_off = 0
    msg.gps_enable = 0
    msg.step_target = 5000

    print msg


if __name__ == '__main__':
    main()