# -*- coding: utf-8 -*-

import threading
import logging
import datetime
import time
import traceback
import random
import hashlib

from tornado import ioloop, gen
import haversine

import auth_mongo_defines as auth_def
import utils

import pymongo

from mongo_dao_base import MongoDAOBase
import error_codes

import type_defines

_OLD_USER_PASSWD_EXTRA_KEY = "k|~58j9t*MzTC2G_=}/(l)$nBsNx&Ub;@i1g0Ymc"


class AuthMongoDAOException(Exception):
    def __init__(self, message, *args):
        self._msg = message % tuple(args)

    def __str__(self):
        return self._msg


class AuthMongoDAO(MongoDAOBase):
    def __init__(self, *args, **kwargs):
        MongoDAOBase.__init__(self, *args, **kwargs)

    def _gen_hash_passwd(self, mobile_num, passwd):
        sha1 = hashlib.sha1()
        sha1.update(passwd)
        user_hashpasswd = sha1.hexdigest()

        salt = "%s%u%u" % (mobile_num, int(time.time() * 10000),
                           random.randint(0, 999999999))
        sha1 = hashlib.sha1()
        sha1.update(salt)
        salt_hash = sha1.hexdigest()

        salt_passwd = user_hashpasswd + salt_hash
        sha1 = hashlib.sha1()
        sha1.update(salt_passwd)
        salt_hashpasswd = sha1.hexdigest()

        return (salt_hashpasswd, salt_hash)

    def _check_passwd(self, upasswd, hashpass, salt):
        sha1 = hashlib.sha1()
        sha1.update(upasswd)
        uhashpasswd = sha1.hexdigest()

        salt_passwd = uhashpasswd + salt
        sha1 = hashlib.sha1()
        sha1.update(salt_passwd)

        return hashpass == sha1.hexdigest()

    def _check_passwd_old_user(self, upasswd, hashpass):
        sha1 = hashlib.sha1()
        sha1.update(upasswd)

        md5 = hashlib.md5()
        md5.update(sha1.hexdigest() + _OLD_USER_PASSWD_EXTRA_KEY)

        return hashpass == md5.hexdigest()

    def _new_verify_code(self, len):
        ret = ""
        for i in range(0, len):
            ret += str(random.randint(0, 9))
        return ret

    @gen.coroutine
    def import_auth_info(self, type, sub_type, mobile_num, auth_id, hashpass,
                         salt):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[auth_def.AUTH_DATABASE][auth_def.AUTH_INFOS_TB]

            row = auth_def.new_auth_infos_row()
            row["type"] = type
            row["sub_type"] = sub_type
            row["auth_id"] = auth_id
            row["mobile_num"] = mobile_num
            row["auth_data"] = {"passwd": hashpass, "salt": salt}

            tb.insert_one(row)

        yield self.submit(_callback)

    @gen.coroutine
    def add_auth_info(self, type, sub_type, mobile_num, auth_id, passwd):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[auth_def.AUTH_DATABASE][auth_def.AUTH_INFOS_TB]

            row = auth_def.new_auth_infos_row()
            row["type"] = type
            row["sub_type"] = sub_type
            row["auth_id"] = auth_id
            row["mobile_num"] = mobile_num

            hashpass, salt = self._gen_hash_passwd(mobile_num, passwd)
            auth_data = {"passwd": hashpass, "salt": salt}
            row["auth_data"] = auth_data

            tb.insert_one(row)

        yield self.submit(_callback)

    """
    添加一个用户认证信息
    """

    @gen.coroutine
    def add_user_auth_info(self, mobile_num, uid, passwd):
        yield self.add_auth_info(type_defines.USER_AUTH,
                                 type_defines.NORMAL_AUTH, mobile_num, uid,
                                 passwd)

    @gen.coroutine
    def has_auth_info_by_mobile_num(self, type, mobile_num):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[auth_def.AUTH_DATABASE][auth_def.AUTH_INFOS_TB]
            cursor = tb.find({"type": type,
                              "mobile_num": mobile_num}, {"_id": 0,
                                                          "auth_id": 1})
            logging.info({"type": type,
                          "mobile_num": mobile_num,
                          "cursor.count()": cursor.count()})
            if cursor.count() <= 0:
                return None
            else:
                return cursor[0]["auth_id"]

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def has_auth_info_by_auth_id(self, type, auth_id):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[auth_def.AUTH_DATABASE][auth_def.AUTH_INFOS_TB]
            cursor = tb.find({"type": type,
                              "auth_id": auth_id}, {"_id": 0,
                                                    "mobile_num": 1})
            if cursor.count() <= 0:
                return None
            else:
                return cursor[0]["mobile_num"]

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def get_auth_info(self, type, auth_id):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[auth_def.AUTH_DATABASE][auth_def.AUTH_INFOS_TB]
            cursor = tb.find({"type": type, "auth_id": auth_id}, {"_id": 0})
            if cursor.count() <= 0:
                return None
            return cursor[0]

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    """
    指定的手机号是否存在用户认证信息
    """

    @gen.coroutine
    def has_user_auth_info_by_mobile_num(self, mobile_num):
        ret = yield self.has_auth_info_by_mobile_num(type_defines.USER_AUTH,
                                                     mobile_num)
        raise gen.Return(ret)

    """
    指定的认证ID是否存在用户认证信息
    """

    @gen.coroutine
    def has_user_auth_info_by_auth_id(self, auth_id):
        ret = yield self.has_auth_info_by_auth_id(type_defines.USER_AUTH,
                                                  auth_id)
        raise gen.Return(ret)

    @gen.coroutine
    def update_passwd(self, auth_type, mobile_num, newpass):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[auth_def.AUTH_DATABASE][auth_def.AUTH_INFOS_TB]

            cursor = tb.find({"type": auth_type,
                              "mobile_num": mobile_num}, {"_id": 0,
                                                          "sub_type": 1})

            hashpass, salt = self._gen_hash_passwd(mobile_num, newpass)
            auth_data = {"passwd": hashpass, "salt": salt}

            set_data = {"$set": {"auth_data": auth_data,
                                 "freq_begin_tm": int(time.time()),
                                 "freq_counter": 0}}
            if cursor[0]["sub_type"] == type_defines.OLD_AUTH:
                set_data["$set"]["sub_type"] = type_defines.OLD_NORMAL_AUTH

            res = tb.update_one({"type": auth_type,
                                 "mobile_num": mobile_num}, set_data)
            return res.modified_count

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    """
    更新用户密码
    """

    @gen.coroutine
    def update_user_passwd(self, mobile_num, newpass):
        ret = yield self.update_passwd(type_defines.USER_AUTH, mobile_num,
                                       newpass)
        raise gen.Return(ret)

    @gen.coroutine
    def check_auth_status(self, type, auth_id):
        def _callback(mongo_client, **kwargs):
            # 得到认证信息
            auth_info_tb = mongo_client[auth_def.AUTH_DATABASE][
                auth_def.AUTH_INFOS_TB]
            cursor = auth_info_tb.find({"type": type, "auth_id": auth_id})
            if cursor.count() <= 0:
                return (error_codes.EC_USER_NOT_EXIST, None)
            auth_info = cursor[0]

            # 检查用户账号是否被冻结
            if auth_info["state"] == type_defines.ST_AUTH_NORMAL:  # 正常
                pass
            elif auth_info[
                    "state"] == type_defines.ST_AUTH_FREEZE_FOREVER:  # 永久冻结
                return (error_codes.EC_ACCOUNT_FREEZED, None)
            elif auth_info[
                    "state"] == type_defines.ST_AUTH_FREEZE_TEMP:  # 账号被临时冻结
                # 检查冻结是否已经过期
                freeze_begin_tm = auth_info["freeze_begin_tm"]
                cur_tm = int(time.time())
                freeze_times = auth_info["freeze_times"]
                if cur_tm - freeze_begin_tm > freeze_times:
                    logging.warning(
                        "Auth freeze is expired, unfreeze it, type=%u auth_id=%s",
                        type, str(auth_id))
                    auth_info_tb.update_one(
                        {"type": type,
                         "auth_id": auth_id},
                        {"$set": {"state": type_defines.ST_AUTH_NORMAL}})
                else:
                    return (error_codes.EC_ACCOUNT_FREEZED_TEMP,
                            freeze_begin_tm + freeze_times - cur_tm)
            else:
                raise AuthMongoDAOException("Unkown auth info state, state=%u",
                                            auth_info["state"])

            return (error_codes.EC_SUCCESS, None)

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    """
    检查用户账号的状态
    """

    @gen.coroutine
    def check_user_auth_status(self, uid):
        ret = yield self.check_auth_status(type_defines.USER_AUTH, uid)
        raise gen.Return(ret)

    @gen.coroutine
    def auth(self,
             type,
             auth_id,
             passwd,
             check_freq=True,
             freq_check_interval=60,
             freq_limit_count=3):
        def _callback(mongo_client, **kwargs):
            # 得到认证信息
            auth_info_tb = mongo_client[auth_def.AUTH_DATABASE][
                auth_def.AUTH_INFOS_TB]
            cursor = auth_info_tb.find({"type": type, "auth_id": auth_id})
            if cursor.count() <= 0:
                return (error_codes.EC_USER_NOT_EXIST, None)
            auth_info = cursor[0]

            # 检查登录失败的频率
            cur_tm = int(time.time())
            if check_freq and cur_tm - auth_info[
                    "freq_begin_tm"] <= freq_check_interval and auth_info[
                        "freq_counter"] >= freq_limit_count:
                return (error_codes.EC_NEED_VERIFY_CODE, None)

            # 登录账号
            check_st = True
            is_old = False
            #if auth_info["sub_type"] == type_defines.NORMAL_AUTH or auth_info["sub_type"] == type_defines.OLD_NORMAL_AUTH:
            #    check_st = self._check_passwd(passwd, auth_info["auth_data"]["passwd"], auth_info["auth_data"]["salt"])
            #elif auth_info["sub_type"] == type_defines.OLD_AUTH:
            #    if type == type_defines.USER_AUTH:
            #        check_st = self._check_passwd_old_user(passwd, auth_info["auth_data"]["passwd"])
            #    else:
            #        raise AuthMongoDAOException("Unknown auth old subtype \"%u\"", auth_info["sub_type"])
            #    is_old = True
            # if check_st:  # 登录成功
            # 重置登录频率计时器
            auth_info_tb.update_one({"type": type,
                                     "auth_id": auth_id},
                                    {"$set": {"freq_begin_tm": cur_tm,
                                              "freq_counter": 0}})

            return (error_codes.EC_SUCCESS, is_old)
            #else:  # 登录失败则需要更新频率限制的计数器
            #    up_data = None
            #    if cur_tm > freq_check_interval + auth_info["freq_begin_tm"]:
            #        updata = {"$set": {"freq_begin_tm": cur_tm,
            #                           "freq_counter": 1}}
            #    else:
            #        updata = {"$inc": {"freq_counter": 1}}
            #    auth_info_tb.update_one({"type": type,
            #                             "auth_id": auth_id}, updata)
            #    return (error_codes.EC_INVALID_PASS, None)

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    """
    用户认证
    """

    @gen.coroutine
    def user_auth(self,
                  uid,
                  passwd,
                  check_freq=True,
                  freq_check_interval=60,
                  freq_limit_count=3):
        ret = yield self.auth(type_defines.USER_AUTH, uid, passwd, check_freq,
                              freq_check_interval, freq_limit_count)
        raise gen.Return(ret)

    @gen.coroutine
    def get_device_info(self, type, auth_id):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[auth_def.AUTH_DATABASE][auth_def.AUTH_STATUS_TB]

            cursor = tb.find({"auth_type": type,
                              "auth_id": auth_id}, {"_id": 0,
                                                    "device_type": 1,
                                                    "device_token": 1})
            if cursor.count() <= 0:
                return None
            return cursor[0]

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    def gen_token(self, type, auth_id, multi_login, device_type, device_token,
                  expire_times, platform, device_model,device_os_int):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[auth_def.AUTH_DATABASE][auth_def.AUTH_STATUS_TB]

            cond = {"auth_type": type, "auth_id": auth_id}
            count = tb.count(cond)

            timestamp = int(time.time() * 10000)
            seek1 = random.randint(0, 999999999)
            seek2 = random.randint(999999999, 2000000000)
            seek3 = random.randint(2000000000, 3000000000)
            seek4 = random.randint(3000000000, 4000000000)
            orig_token = "%s%u%s%u%u%u%u%s%u" % (
                str(auth_id), timestamp, str(device_type), seek1, seek2, seek3,
                seek4, str(device_token), count + 1)
            sha1 = hashlib.sha1()
            sha1.update(orig_token)
            token = sha1.hexdigest()

            row = auth_def.new_auth_status_row()
            row["auth_type"] = type
            row["auth_id"] = auth_id
            row["token"] = token
            row["device_type"] = device_type
            row["device_token"] = device_token
            row["expire_times"] = expire_times
            row["platform"] = platform
            row["device_model"] = device_model
            row["device_os_int"]=device_os_int

            if not multi_login:
                tb.delete_many(cond)

            tb.insert_one(row)

            return token

        return self.submit(_callback)

    """
    生成用户token
    """

    def gen_user_token(self, uid, multi_login, device_type, device_token,
                       expire_times, platform, device_model,device_os_int):
        return self.gen_token(type_defines.USER_AUTH, uid, multi_login,
                              device_type, device_token, expire_times,
                              platform, device_model,device_os_int)

    # def get_cur_login_info(self, type, auth_id):
    #    info = {}
    #    tb = mongo_client[auth_def.AUTH_DATABASE][auth_def.AUTH_STATUS_TB]
    #    return tb.find_one({"auth_type": type,
    #                        "auth_id": auth_id}, sort=[("add_date", pymongo.DESCENDING)])

    def check_token(self, type, auth_id, token):
        def _callback(mongo_client, **kwargs):
            # 检查token状态
            ec = error_codes.EC_SUCCESS
            info = {}
            tb = mongo_client[auth_def.AUTH_DATABASE][auth_def.AUTH_STATUS_TB]

            info = tb.find_one({"auth_type": type,
                                "auth_id": auth_id},
                               sort=[("add_date", pymongo.DESCENDING)])

            if info is None:
                ec = error_codes.EC_INVALID_TOKEN
            else:
                if info["state"] == 0:
                    ec = error_codes.EC_INVALID_TOKEN
                elif info["token"] != token:
                        ec = error_codes.EC_LOGIN_IN_OTHER_PHONE
                elif info["expire_times"] != 0:
                    tm = utils.date2int(info["mod_date"]) + info[
                        "expire_times"]
                    cur_tm = int(time.time())
                    if cur_tm >= tm:  # 已经过期
                        ec = error_codes.EC_TOKEN_EXPIRED
            return ec, info

        return self.submit(_callback)

    """
    检查用户token
    """

    def check_user_token(self, uid, token):
        return self.check_token(type_defines.USER_AUTH, uid, token)

    @gen.coroutine
    def delete_token(self, type, auth_id, token):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[auth_def.AUTH_DATABASE][auth_def.AUTH_STATUS_TB]
            tb.delete_one({"auth_type": type,
                           "auth_id": auth_id,
                           "token": token})

        yield self.submit(_callback)

    """
    删除用户token
    """

    @gen.coroutine
    def delete_user_token(self, uid, token):
        yield self.delete_token(type_defines.USER_AUTH, uid, token)

    @gen.coroutine
    def delete_all_tokens(self, type, auth_id):
        def _callback(mongo_client, **kwargs):
            tb = mongo_client[auth_def.AUTH_DATABASE][auth_def.AUTH_STATUS_TB]
            tb.delete_many({"auth_type": type, "auth_id": auth_id})

        yield self.submit(_callback)

    @gen.coroutine
    def delete_user_all_tokens(self, uid):
        yield self.delete_all_tokens(type_defines.USER_AUTH, uid)

    """
    len  验证码的长度
    expire_times 过期时间以秒为单位
    interval   距离上一次请求的必须的间隔时间，以秒为单位
    freq_check_interval 频率检查间隔
    freq_limit_count 在一个频率检查间隔内的最大请求数量
    """

    @gen.coroutine
    def gen_verify_code(self, auth_type, type, mobile_num, len, expire_times,
                        interval, freq_check_interval, freq_limit_count):
        if type not in type_defines.VERIFY_CODE_TYPES:
            raise AuthMongoDAOException("Unknown verify code type, type=%u",
                                        type)

        def _callback(mongo_client, **kwargs):
            tb = mongo_client[auth_def.AUTH_DATABASE][
                auth_def.VERIFY_CODE_STATUS_TB]
            cond = {"auth_type": auth_type,
                    "type": type,
                    "mobile_num": mobile_num}
            info = None
            cursor = tb.find(cond)
            if cursor.count() > 0:
                info = cursor[0]
            if info is None:  # 不存在则创建
                code = self._new_verify_code(len)
                row = auth_def.new_verify_code_status_row()
                row["auth_type"] = auth_type
                row["type"] = type
                row["mobile_num"] = mobile_num
                row["code"] = code
                row["freq_counter"] = 1
                row["expire_times"] = expire_times
                tb.insert_one(row)
                return (code, error_codes.EC_SUCCESS, None)

# 首先检查距离上一次请求的时间间隔
            pre_tm = utils.date2int(info["mod_date"])
            cur_tm = int(time.time())
            if cur_tm - pre_tm <= interval:
                return (None, error_codes.EC_FREQ_LIMIT,
                        pre_tm + interval - cur_tm)

            # 检查频率
            freq_begin_tm = info["freq_begin_tm"]
            if cur_tm > freq_begin_tm + freq_check_interval:  # 频率定时器已经过期
                code = self._new_verify_code(len)
                tb.update_one(cond, {"$set": {"code": code,
                                              "expire_times": expire_times,
                                              "mod_date":
                                              datetime.datetime.today(),
                                              "freq_begin_tm": cur_tm,
                                              "freq_counter": 1}})
                return (code, error_codes.EC_SUCCESS, None)
            elif info["freq_counter"] >= freq_limit_count:  # 超出频率限制
                return (None, error_codes.EC_FREQ_LIMIT,
                        freq_begin_tm + freq_check_interval - cur_tm)
            else:  # 正常请求
                code = self._new_verify_code(len)
                tb.update_one(cond, {"$inc": {"freq_counter": 1},
                                     "$set": {"code": code,
                                              "expire_times": expire_times,
                                              "mod_date":
                                              datetime.datetime.today()}})
                return (code, error_codes.EC_SUCCESS, None)

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def gen_user_verify_code(self, type, mobile_num, len, expire_times,
                             interval, freq_check_interval, freq_limit_count):
        ret = yield self.gen_verify_code(
            type_defines.USER_AUTH, type, mobile_num, len, expire_times,
            interval, freq_check_interval, freq_limit_count)
        raise gen.Return(ret)

    @gen.coroutine
    def check_verify_code(self, auth_type, type, mobile_num, verify_code):
        if type not in type_defines.VERIFY_CODE_TYPES:
            raise AuthMongoDAOException("Unknown verify code type, type=%u",
                                        type)

        def _callback(mongo_client, **kwargs):
            tb = mongo_client[auth_def.AUTH_DATABASE][
                auth_def.VERIFY_CODE_STATUS_TB]

            cond = {"auth_type": auth_type,
                    "type": type,
                    "mobile_num": mobile_num}
            info = None
            cursor = tb.find(cond)
            if cursor.count() > 0:
                info = cursor[0]
            else:
                return error_codes.EC_INVALID_VERIFY_CODE

            if info["code"] != verify_code:
                return error_codes.EC_INVALID_VERIFY_CODE

            tm = utils.date2int(info["mod_date"])
            cur_tm = int(time.time())
            if cur_tm > tm + info["expire_times"]:
                return error_codes.EC_VERIFY_CODE_EXPIRED

            return error_codes.EC_SUCCESS

        ret = yield self.submit(_callback)
        raise gen.Return(ret)

    @gen.coroutine
    def check_user_verify_code(self, type, mobile_num, verify_code):
        ret = yield self.check_verify_code(type_defines.USER_AUTH, type,
                                           mobile_num, verify_code)
        raise gen.Return(ret)
