# -*- coding: utf-8 -*-

import time
import datetime


def change_unescape_ssid(mac):
    if can_unicode(mac):
        return mac
    else:
        normal = []
        tmp = mac.split("|")
        for item in tmp:
            if item != "" and can_unicode(item):
                normal.append(item)
        if len(normal) != 0:
            return "|".join(normal)
        return ""


def split_locator_station_info(locator_station):
    tmp = locator_station.split("|")
    if len(tmp) == 1:
        return tmp[0], None
    else:
        return tmp[0], "|".join(tmp[1:])


def can_unicode(strstr):
    try:
        unicode(strstr)
    except Exception, e:
        return False
    else:
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


def change_sleep_data(begin_time, secs):
    ret = []
    beign_dt = begin_time
    end_dt = beign_dt + datetime.timedelta(seconds=secs)
    tmp = beign_dt
    tmp2 = datetime.datetime.combine(beign_dt, datetime.time.max)

    while 1:
        if end_dt < tmp2:
            ret.append(
                (tmp.date(), int(round((end_dt - tmp).total_seconds()))))
            break
        else:
            ret.append((tmp.date(), int(round((tmp2 - tmp).total_seconds()))))
            tmp = tmp2 + datetime.timedelta(seconds=1)
            tmp2 = tmp2 + datetime.timedelta(days=1)
    return ret


def main():
    print split_locator_station_info(
        "460,0,9365,4190,42|460,0,9365,5281,22|460,0,9365,4052,13|460,0,9365,3701,11|460,0,9365,4213,8|460,0,9365,5042,7|460,0,9365,4832,6")


if __name__ == '__main__':
    main()