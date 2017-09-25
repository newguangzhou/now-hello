# -*- coding: utf-8 -*-
import json


def new_device_off_line_msg():
    msg = {"type": "device",
           "signal": "offline",
           }
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")

def new_device_on_line_msg(battery,datetime):
    msg = {"type": "device",
           "signal": "online",
           "data": {"battery_level": battery,
                    "datetime":datetime} }
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")

def new_pet_not_home_msg():
    msg = {"type": "pet",
           "signal": "not-home", }
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")

def new_pet_in_home_msg():
    msg = {"type": "pet",
           "signal": "home", }
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")


def new_location_change_msg(latitude, longitude, location_time, radius):
    msg = {"type": "pet",
           "signal": "location-change",
           "data": {
               "latitude": latitude,
               "location_time": location_time,
               "longitude": longitude,
               "radius": radius
           }}
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")

# 0 is common-battery
# 1 is low-battery
# 2 is ultra-low-battery
def new_now_battery_msg(datetime, battery, battery_status):
    signal = "common-battery"
    if battery_status == 1:
        signal = "low-battery"
    elif battery_status == 2:
        signal = "ultra-low-battery"
    msg = {"type": "device",
           "signal": signal,
           "data": {"battery_level": battery,
                    "datetime":datetime}}
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")


def new_remot_login_msg():
    msg = {"type": "user",
           "signal": "remote-login",
           "data": {"remote_login_time": "2017",
                    "X_OS_Name": "xiaominote"}}
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")
