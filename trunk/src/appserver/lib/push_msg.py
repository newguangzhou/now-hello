# -*- coding: utf-8 -*-
import json

#CLIENT_TYPE
CT_IOS       = 1 #IOS
CT_ANDROID   = 2 #ANDROID
def android_msg(msg):
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")
def ios_msg(msg):
    new_msg = {}
    if msg.has_key("data"):
        for k,v in msg.items():
            if k == "data":
                for k1,v1 in v.items():
                    new_msg[k1] = v1
            else:
                new_msg[k] = v
        return json.dumps(new_msg, ensure_ascii=False, encoding="utf8")
    else:
        return json.dumps(msg, ensure_ascii=False, encoding="utf8")

def new_device_off_line_msg(offline_reason, client_type = CT_ANDROID):
    msg = {"type": "device",
           "signal": "offline",
           "data" : {
               "offline_reason": offline_reason
                }
           }
    if client_type == CT_IOS:
        return ios_msg(msg)
    else:
        return json.dumps(msg, ensure_ascii=False, encoding="utf8")

def new_device_on_line_msg(battery,datetime):
    msg = {"type": "device",
           "signal": "online",
           "data": {"battery_level": battery,
                    "datetime":datetime} }
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")

def new_pet_outdoor_in_portected_msg(client_type, pet_id, name):
    msg = {"type": "pet",
           "signal": "outdoor_in_protected",
           "data":
               {
                   "pet_id":pet_id,
                   "name":name
               }
           }
    if client_type == CT_IOS:
        return ios_msg(msg)
    else:
        return android_msg(msg)

def new_pet_outdoor_out_portected_msg(client_type, pet_id, name):
    msg = {"type": "pet",
           "signal": "outdoor_out_protected",
           "data":
               {
                   "pet_id":pet_id,
                   "name":name
               }
           }
    if client_type == CT_IOS:
        return ios_msg(msg)
    else:
        return android_msg(msg)

def new_pet_leave_home_msg(client_type, pet_id ,name):
    msg = {"type": "pet",
           "signal": "not-home",
           "data":
               {
                   "pet_id":pet_id,
                   "name":name
               }
           }
    if client_type == CT_IOS:
        return ios_msg(msg)
    else:
        return android_msg(msg)

def new_pet_at_home_msg(client_type, pet_id, name):
    msg = {"type": "pet",
           "signal": "home",
           "data":
               {
                   "pet_id":pet_id,
                   "name":name
               }
           }
    if client_type == CT_IOS:
        return ios_msg(msg)
    else:
        return android_msg(msg)


def new_location_change_msg(client_type = CT_ANDROID, **kwargs):
    #pet_id,name, latitude, longitude, location_time, radius, locator_status, station_status
    msg = {"type": "pet",
           "signal": "location-change",
           "data": { kwargs
           }}
    if client_type == CT_IOS:
        return ios_msg(msg)
    else:
        return android_msg(msg)

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

def extra(raw):
    return json.dumps(raw,ensure_ascii=False, encoding="utf8")
