# -*- coding: utf-8 -*-

import datetime
import time
import logging
import copy
import re
from tornado.concurrent import Future
from tornado import gen
import math
from sys_config import DOG_CONFIG, DOG_NAME_CONFIG


def date2str(dt, no_time=False):
    if isinstance(dt, datetime.datetime):
        if no_time:
            return "%02u-%02u-%02u" % (dt.year, dt.month, dt.day)
        else:
            return "%02u-%02u-%02u %02u:%02u:%02u" % (
                dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    elif isinstance(dt, datetime.date):
        return "%02u-%02u-%02u" % (dt.year, dt.month, dt.day)
    else:
        return ""


def str2date(str, format="%Y%m%d"):
    st = time.strptime(str, format)
    return datetime.date.fromtimestamp(time.mktime(st))


def str2datetime(str, format="%Y%m%d%H%M%S"):
    st = time.strptime(str, format)
    return datetime.datetime.fromtimestamp(time.mktime(st))
def stamp2data(stamp,format='%Y-%m-%d %H:%M:%S'):
    x=time.localtime(stamp)
    data_string=time.strftime('%Y-%m-%d %H:%M:%S',x)
    yesr=int(data_string[0:4])
    month=int(data_string[5:7])
    day=int(data_string[8:10])
    H=int(data_string[11:13])
    M=int(data_string[14:16])
    S=int(data_string[17:19])
    return datetime.datetime(yesr, month, day, H, M, S)
'''
0:time1小
1:time1大
'''
def compare_time(time1,time2):
    i_time1 = date2int(time1)
    i_time2 = date2int(time2)
    if i_time1 < i_time2:
        return 0
    else:
        return 1

def date2int(dt):
    return int(time.mktime(dt.timetuple()))


def gen_select_sql(table, fnames, cond, iswhere=True, limit=None):
    sql = "select "
    for i in range(0, len(fnames)):
        sql += fnames[i]
        if i != len(fnames) - 1:
            sql += ","
    sql += " from %s " % (table, )
    if cond is not None:
        if iswhere:
            sql += "where "
        sql += cond
    if limit is not None:
        sql += "limit %u" % limit
    return sql


def gen_update_sql(table, cond, fnames):
    sql = "update %s set " % (table)
    for i in range(0, len(fnames)):
        sql += fnames[i] + "=%s"
        if i != len(fnames) - 1:
            sql += ","
    if cond is not None:
        sql += " where %s" % (cond, )
    return sql


def gen_insert_sql(table, fnames):
    sql1 = "insert into %s(" % (table, )
    sql2 = " values("
    for i in range(0, len(fnames)):
        sql1 += fnames[i]
        sql2 += "%s"
        if i != len(fnames) - 1:
            sql1 += ","
            sql2 += ","
    sql1 += ")"
    sql2 += ")"

    return sql1 + sql2


def recover_log(title, **kwargs):
    msg = "[recover] title=\"%s\"," % (title, )
    i = 0
    for (k, v) in kwargs.items():
        if isinstance(v, int) or isinstance(v, float):
            msg += "%s=%s" % (k, str(v))
        elif isinstance(v, str):
            msg += "%s=\"%s\"" % (k, v)
        else:
            msg += "%s=\"%s\"" % (k, str(v))
        if i != len(kwargs) - 1:
            msg += ","
        i += 1
    logging.error(msg)


def new_mongo_row(row_define):
    tmp = copy.deepcopy(row_define)
    ret = {}
    for (k, v) in tmp.items():
        ret[k] = v[0]
    return ret


def validate_mongo_row(row, row_define):
    print row, row_define
    for (k, v) in row.items():
        if v is None:
            return (False, k)

        if not row_define.has_key(k):
            print 1, k, v
            return (False, k)

        if not isinstance(v, row_define[k][1]):
            print 2, k, v, row_define[k][1], type(v)
            return (False, k)
    return (True, None)


def validate_mongo_row_cols(row_define, **cols):
    for (k, v) in cols.items():
        if not row_define.has_key(k):
            return (False, k)
        if not isinstance(v, row_define[k][1]):
            return (False, k)
    return (True, None)


def has_mongo_row_col(row_define, colname):
    return row_define.has_key(colname)


def is_mobile_num(val):
    if len(val) != 11:
        return False

    for c in val:
        try:
            int(c)
        except:
            return False

    if val[0] == '0':
        return False

    return True


def merge(times):
    saved = list(times[0])
    ret = []
    for st, en in sorted([sorted(t) for t in times]):
        if st <= saved[1]:
            saved[1] = max(saved[1], en)
        else:
            ret.append(tuple(saved))
            saved[0] = st
            saved[1] = en
    ret.append(tuple(saved))
    return ret


def is_valid_phone_num(phone_num):
    p = re.compile(
        '^((13[0-9])|(14[0-9])|(15[0-9])|(16[0-9])|(17[0-9])|(18[0-9]))\d{8}$')
    return p.match(phone_num)


def calculate_dog_sport(month, weight, id, default_id=0):
    sport = 0
    dog_info = DOG_CONFIG.get(id, None)
    if dog_info is None:
        dog_info = DOG_CONFIG.get(default_id, None)
    if dog_info is not None:
        sport = _calculate_dog_sport(month, weight, dog_info)
    return sport


def calculate_dog_sport_by_name(month, weight, name, default_name):
    sport = 0
    dog_info = DOG_NAME_CONFIG.get(name, "")
    if dog_info is None:
        dog_info = DOG_NAME_CONFIG.get(default_name, "")
    if dog_info is not None:
        sport = _calculate_dog_sport(month, weight, dog_info)
    return sport


def _calculate_dog_sport(month, weight, dog_info):
    ere = math.pow(math.pow(70 * weight, 3), 1.0 / 4)
    if 0 <= month <= 4:
        sport = dog_info["rer_config"][0] * ere
    elif 4 < month <= 96:
        sport = dog_info["rer_config"][1] * ere
    else:
        sport = dog_info["rer_config"][2] * ere
    return sport


def change_wifi_info(mac, need_deep=False):
    ret = []
    tmp = mac.split("|")
    for item in tmp:
        if item != "":
            tmp2 = item.split(",")
            print "tmp2:", tmp2
            if len(tmp2) != "":
                info = {"wifi_ssid": tmp2[2], "wifi_bssid": tmp2[0]}
                if need_deep:
                    info["deep"] = tmp2[1]
                ret.append(info)
            #for item2 in tmp2:

    return ret

def is_imei_valide(imei):
    if imei is None or len(imei)<>15 or imei.find('35739608')<>0:
        return False
    list = []
    index = 0
    eSum = 0
    iSum = 0
    for item in imei:
        value = int(item)
        if index < 14:
            if index % 2 == 0:
                eSum += value
            else:
                iSum += (int(value * 2 / 10) + (value * 2 % 10))
        list.append(value)
        index += 1
    # print("--iSum--%d",iSum)
    # print("--eSum--%d",eSum)
    # print list
    imei15 = (10 - ((eSum + iSum) % 10)) % 10
    # print imei15
    if imei15 == list[14]:
        return True
    else:
        return False

def is_in_home(home_wifi,common_wifi,wifi_list):
    wifi_list_names = []
    #如果没有设置homewifi,直接判定在家
    if home_wifi is None:
        return True
    # 如果有homewifi,判定在家
    for item in wifi_list:
        wifi_list_names.append(item["wifi_ssid"])
        if home_wifi is not None and home_wifi[
            "wifi_bssid"] == item[
            "wifi_bssid"]:
            return True
    # 如果没有homewifi,有3个commonwifi在列表里，
    num = 0
    if common_wifi is not None:
         for item in wifi_list_names:
             for item2 in common_wifi:
              if item == item2["wifi_ssid"]:
                 num += 1;
                 if num > 2:
                     return True
    # 如果没有homewifi,不含用户设定的HomeWifi，但扫到的wifi < 6个，如果其中 >50% 以上的wifi在wifi列表中，则认为追踪器状态为：在家。
    wifi_list_size=len(wifi_list)
    num = 0
    if wifi_list_size<6:
        for item in wifi_list_names:
            for item2 in common_wifi:
              if item == item2["wifi_ssid"]:
                 num+=1
        if num>wifi_list_size/2:
            return True

    return False

def get_new_common_wifi(common_wifi,wifi_info,home_wifi):
    if home_wifi is None:
        logging.debug("home_wifi is None in get_new_common_wifi")
        common_wifi = []
        return common_wifi
    alpha = 2
    beta = 1
    home_wifi_power = None
    home_wifi_bssid = home_wifi["wifi_bssid"]
    for item in wifi_info:
        if item["wifi_bssid"] == home_wifi_bssid:
            home_wifi_power = int(item.get("deep",-100))
            break

    if common_wifi is None:
        common_wifi = []
    else:
        pre_seven_days_datetime = datetime.datetime.now() + datetime.timedelta(days=-7)
        for item in common_wifi:
            item_create_time = item.get("create_time", datetime.datetime.now())
            if compare_time(pre_seven_days_datetime,item_create_time):
                common_wifi.remove(item)
                continue
            if home_wifi_power is not None:
                item_power = int(item.get("deep", -100))
                item_cal = alpha * home_wifi_power+ beta * item_power
                item["cal"] = item_cal

    if home_wifi_power is None or home_wifi_power < -99:
        if home_wifi_power is None:
            logging.debug("home_wifi_power is None in get_new_common_wifi")
        else:
            logging.debug("home_wifi_power < -99 in get_new_common_wifi：%d" % home_wifi_power)
        return common_wifi


    create_time = datetime.datetime.now()
    for item in wifi_info:
        item_power = int(item.get("deep",-100))
        item_cal = alpha * home_wifi_power+ beta * item_power
        item["cal"] = item_cal
        item["create_time"] = create_time
        if len(common_wifi) < 10:
            for item1 in common_wifi:
                if item1["wifi_bssid"]==item["wifi_bssid"]:
                    common_wifi.remove(item1)
            common_wifi.append(item)
        else:
            for common_item in common_wifi:
                common_item_cal = common_item["cal"]
                if common_item_cal < item_cal:
                    common_wifi.remove(common_item)
                    for item1 in common_wifi:
                        if item1["wifi_bssid"] == item["wifi_bssid"]:
                            common_wifi.remove(item1)
                    common_wifi.append(item)
                    break
    return common_wifi
def get_new_common_wifi_from_client(common_wifi,wifi_info,home_wifi):
    if home_wifi is None:
        logging.debug("home_wifi is None in get_new_common_wifi")
        common_wifi = []
        return common_wifi
    alpha = 2
    beta = 1
    home_wifi_power = None
    home_wifi_bssid = home_wifi["wifi_bssid"]
    for item in wifi_info:
        if item["wifi_bssid"] == home_wifi_bssid:
            home_wifi_power = int(item.get("wifi_power",-100))
            break
    if common_wifi is None:
        common_wifi = []
    if home_wifi_power is None or home_wifi_power < -99:
        if home_wifi_power is None:
            logging.debug("home_wifi_power is None in get_new_common_wifi")
        else:
            logging.debug("home_wifi_power < -99 in get_new_common_wifi：%d" % home_wifi_power)
        return common_wifi


    create_time = datetime.datetime.now()
    for item in wifi_info:
        item_power = int(item.get("wifi_power",-100))
        item_cal = alpha * home_wifi_power+ beta * item_power
        item["cal"] = item_cal
        # item["create_time"] = create_time
        if len(common_wifi) < 10:
            common_wifi.append(item)
        else:
            for common_item in common_wifi:
                common_item_cal = common_item["cal"]
                if common_item_cal < item_cal:
                    common_wifi.remove(common_item)
                    common_wifi.append(item)
                    break
    return common_wifi
#电量级别是否相等
def battery_status_isequal(localbattery_status,nowbattery_status):
    if (localbattery_status is None or localbattery_status ==0) and nowbattery_status==0:
        return True
    if localbattery_status == nowbattery_status:
        return True
    return False

#卡路里转换
# 如果性别 = 公，
# 卡路里 = 设备卡路里 x 体重 / 15.00  x【定义的系数】
# 如果性别 = 母，
# 卡路里 = 设备卡路里 x 体重 / 15.00 x 1.10 / 1.29 x【定义的系数】
# 【定义的系数】暂时设为1，后面可能会不断微调……
def calorie_transform(raw_calorie,weight,sex,coefficient=1):
    result_calorie=raw_calorie
    if sex==1:
        #公
        result_calorie=raw_calorie*weight*coefficient/15.00
    elif sex==2:
        result_calorie=raw_calorie*weight*coefficient*1.10/(1.29*15.00)
    return result_calorie





