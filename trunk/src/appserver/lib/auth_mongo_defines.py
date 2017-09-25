# -*- coding: utf-8 -*-

import copy
import datetime
import time

import pymongo
from pymongo.operations import IndexModel

AUTH_DATABASE = "xmq_auth"
""" 
认证信息
"""
AUTH_INFOS_TB = "auth_infos"
AUTH_INFOS_TB_INDEXES = [
    IndexModel([("type", pymongo.ASCENDING), ("auth_id", pymongo.ASCENDING)],
               unique=True),
    IndexModel(
        [("type", pymongo.ASCENDING), ("mobile_num", pymongo.ASCENDING)],
        unique=True),
    IndexModel("add_date"),
    IndexModel("mod_date"),
    IndexModel("state"),
]
_AUTH_INFOS_TB_ROW_DEFINE = {
    "type": None,  # 认证类型，1为普通用户
    "sub_type": None,  # 认证子类型，1为普通
    "auth_id": None,  # 认证ID， 和认证类型相关, type + auth_id 必须全局唯一
    "mobile_num": None,  # 手机号码
    "auth_data": None,  # 认证相关信息, 依据不同的认证类型而不同
    "state": 1,  # 状态，1为正常，2为永久冻结，3为临时冻结
    "freeze_begin_tm": 0,  # 冻结开始的时间戳
    "freeze_times": 0,  # 冻结时常，以秒为单位
    "freq_begin_tm": None,  # 频率检查的开始计时器时间戳
    "freq_counter": 0,  # 频率检查的计数器
    "add_date": None,
    "mod_date": None
}


def new_auth_infos_row():
    tmp = copy.deepcopy(_AUTH_INFOS_TB_ROW_DEFINE)
    cur = datetime.datetime.today()
    tmp["add_date"] = cur
    tmp["mod_date"] = cur
    tmp["freq_begin_tm"] = int(time.time())
    return tmp


"""
验证码状态
"""
VERIFY_CODE_STATUS_TB = "verify_code_status"
VERIFY_CODE_STATUS_TB_INDEXES = [
    IndexModel([("auth_type", pymongo.ASCENDING), ("type", pymongo.ASCENDING),
                ("mobile_num", pymongo.ASCENDING)],
               unique=True), IndexModel("add_date")
]
_VERIFY_CODE_STATUS_TB_ROW_DEFINE = {
    "auth_type": None,  # 认证类型，1为普通用户，3为店铺认证
    "type": None,  # 验证码类型，1注册验证码，2登录验证码，3密码找回验证码
    "code": None,  # 验证码
    "mobile_num": None,  # 手机号码
    "add_date": None,  # 初次添加时间
    "mod_date": None,  # 最后修改时间
    "freq_begin_tm": None,  # 频率限制的开始时间
    "freq_counter": 0,  # 频率限制的计数器
    "expire_times": 0  # 过期时间以秒为单位，为0代表永不过期
}


def new_verify_code_status_row():
    tmp = copy.deepcopy(_VERIFY_CODE_STATUS_TB_ROW_DEFINE)
    cur = datetime.datetime.today()
    tmp["add_date"] = cur
    tmp["mod_date"] = cur
    tmp["freq_begin_tm"] = int(time.time())
    return tmp


"""
登录状态
"""
AUTH_STATUS_TB = "auth_status"
AUTH_STATUS_TB_INDEXES = [
    IndexModel([("auth_type", pymongo.ASCENDING),
                ("auth_id", pymongo.ASCENDING), ("token", pymongo.ASCENDING)]),
    IndexModel("device_type"), IndexModel("add_date"), IndexModel("mod_date")
]
_AUTH_STATUS_TB_ROW_DEFINE = {
    "auth_type": None,  # 认证类型
    "auth_id": None,  # 认证标识
    "token": None,  # 认证token
    "expire_times": 0,  # 过期时间，为0代表为永不过期，以秒为单位
    "device_type": None,  # 设备类型
    "device_token": None,  # 设备token
    "device_os_int":(23,int),  #android 设备os  int 值
    "device_model": None,  # 设备型号
    "platform": 0,  #平台
    "state": 1,  # 状态，1正常，0无效
    "add_date": None,
    "mod_date": None
}


def new_auth_status_row():
    tmp = copy.deepcopy(_AUTH_STATUS_TB_ROW_DEFINE)
    cur = datetime.datetime.today()
    tmp["add_date"] = cur
    tmp["mod_date"] = cur
    return tmp
