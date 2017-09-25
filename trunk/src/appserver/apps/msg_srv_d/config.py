# -*- coding: utf-8 -*-


class Config:
    def __init__(self):
        self.proctitle = "msg_srv_d"  # 进程名
        self.test_mode = True  # 是否为测试模式

        self.ymrt_cdkey = "6SDK-EMY-6688-KKVUN"  # 亿美软通的cdkey
        self.ymrt_passwd = "066884"  # 亿美软通的密码

        self.nexmo_key = "c898a8a3"
        self.nexmo_secret = "d5c75dc8"

        self.default_push_title = "小毛球"
        self.mipush_host = "api.xmpush.xiaomi.com"
        self.mipush_appsecret_android = "aQLLX8h129sPKm3NeY9lcA=="
        self.mipush_appsecret_ios = "Cy4/cc5TazG663ClQpkgJg=="
        self.mipush_bundle_id = "com.xiaomaoqiu.catchpet"
        self.mipush_pkg_name = "com.xiaomaoqiu.pet"
        self.dayu_appkey = "23566149"
        self.dayu_secret = "f95d87510975317c9539d858c010f5a0"
