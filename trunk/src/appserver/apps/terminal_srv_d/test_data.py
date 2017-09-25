# -*- coding: utf-8 -*-

from terminal_base import terminal_commands, terminal_packets

params = terminal_commands.Params()
params.report_time = 10  # 分时段上报间隔，以分钟位单位最大值为60
params.add_friend = 0
params.step_enable = 0
params.profile = 1
params.love = 1
params.remote_alert = "18222122212"
params.low_power = 0
params.sos = 0
params.take_off = 1
params.gps_enable = 1
params.step_target = 5000

pet_location = terminal_commands.PetLocation()
pet_location.battery_threshold = 20
pet_location.history_location_switch = 0
pet_location.light_flash = [(1, 5), (1, 7)]
pet_location.pet_heght = "15.2"
pet_location.pet_gender = 1
pet_location.server_ip = "127.0.0.1"
pet_location.server_port = 5050

TEST_S2C_COMMAND_DATA = {
    "005": params,
    "012": terminal_commands.UploadInterval(("0900", "1100", "1111111", 4),
                                            ("1100", "1200", "1111111", 4)),
    "013": terminal_commands.StepInterVal(2, ("0900", "1100"),
                                          ("1200", "1400")),
    "015": terminal_commands.TermimalReset(),
    "017": pet_location,
    "007": terminal_commands.RemotePowerOff(),
}
#print TEST_S2C_COMMAND_DATA.get("005")

#TEST_S2C_GET_LOCATION = terminal_packets.GetLocationAck()