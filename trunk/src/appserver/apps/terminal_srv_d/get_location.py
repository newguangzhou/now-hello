# -*- coding: utf-8 -*-

import urllib, urllib2
import logging
import json
from hashlib import md5
GAODE_POSTION_URL = "http://apilocate.amap.com/position"
GAODE_CONVERT_COORDINATE_URL = "http://restapi.amap.com/v3/assistant/coordinate/convert"
logger = logging.getLogger(__name__)

#基站定位
GAODE_KEY = "86f42db8d4dc316cf14664be0d378ed5"
GAODE_WEB_KEY = "698fcddb6a3afcbe29ea5e831a13af62"
GAODE_WEB_SIGN = "1709e37ad6c51c02381a50cca9fdc5ec"


def convert_coordinate(locations_array, coordsys):
    locations = "%.6f,%.6f" % (locations_array[0], locations_array[1])
    data = {"coordsys": coordsys, "key": GAODE_WEB_KEY, "locations": locations}
    sign_str = "coordsys=%s&key=%s&locations=%s" % (coordsys,
                                                    GAODE_WEB_KEY,
                                                    locations, )
    sign_str += GAODE_WEB_SIGN
    data["sig"] = md5(sign_str).hexdigest()
    data = urllib.urlencode(data)
    try:
        respone = urllib2.urlopen(GAODE_CONVERT_COORDINATE_URL, data, 5)
        response_data = respone.read()
        logger.debug("data:%s convert_coordinate :%s", data, response_data)
        print response_data
        ret_json = json.loads(response_data)
    except Exception, e:
        logger.exception(e)
    else:
        if ret_json["status"] == "1":
            locations_str = ret_json.get("locations", None)
            if locations_str is not None:
                tmp = locations_str.split(",")
                if len(tmp) == 2:
                    return float(tmp[0]), float(tmp[1])
    return None


def get_data_from_gaode(data):
    data = urllib.urlencode(data)
    try:
        respone = urllib2.urlopen(GAODE_POSTION_URL, data, 5)
        response_data = respone.read()
        logger.debug("data:%s get_data_from_gaode :%s", data, response_data)
        print response_data
        ret_json = json.loads(response_data)
    except Exception, e:
        logger.exception(e)
    else:
        if ret_json["status"] == "1":
            result = ret_json["result"]
            location = result.get("location", None)
            radius = result.get("radius", -1)
            if location is None:
                return None
            else:
                tmp = location.split(",")
                if len(tmp) == 2:
                    return float(tmp[0]), float(tmp[1]), int(radius)

    return None


def get_location_by_bts_info(imei, bts_info, near_bts_infos):
    data = {
        "key": GAODE_KEY,
        "accesstype": 0,
        "imei": imei,
        "cdma": 0,
        "network": "GPRS",
        "bts": bts_info,
        "output": "json"
    }
    if near_bts_infos is not None:
        data["nearbts"] = near_bts_infos
    return get_data_from_gaode(data)


def get_location_by_wifi(imei, macs):
    data = {
        "key": GAODE_KEY,
        "accesstype": 1,
        "imei": imei,
        "macs": macs,
        "output": "json"
    }
    return get_data_from_gaode(data)


def get_location_by_mixed(imei, bts_info, near_bts_infos, macs):
    data = {"key": GAODE_KEY, "imei": imei, "output": "json"}
    if bts_info is not None:
        data["accesstype"] = 0
        data["bts"] = bts_info
        data["cdma"] = 0
        data["network"] = "GPRS"
        if near_bts_infos is not None:
            data["nearbts"] = near_bts_infos
    if macs is not None:
        if not data.has_key("accesstype"):
            data["accesstype"] = 1
        data["macs"] = macs
    return get_data_from_gaode(data)


def main():
    #macs = "24:69:68:54:e4:0e,-87,UNKOWN|1c:de:a7:c4:e6:83,-79,UNKOWN"
    #print get_location_by_wifi("358688000000152", macs)
    print convert_coordinate((116.481499, 39.990475), "gps")


if __name__ == '__main__':
    main()