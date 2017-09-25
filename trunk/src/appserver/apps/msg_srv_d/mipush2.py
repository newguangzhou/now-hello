# -*- coding: utf-8 -*-
"""
使用官方的sdk
"""

import json
import logging

from APISender import APISender
from base.APIMessage import *
from base.APIConstants import Constants


class MiPush2:
    def __init__(self, appsecret_android, app_pkg_name, appsecret_ios, bundle_id, debug_mode):
        # Constants.use_official()
        # Constants.use_sandbox()
        self._appsecret_android = appsecret_android
        self._appsecret_ios = appsecret_ios
        self._bundle_id = bundle_id
        self._app_pkg_name = app_pkg_name
        self._debug_mode = debug_mode
        self._sender_android = APISender(self._appsecret_android)
        self._sender_ios = APISender(self._appsecret_ios)

    def send_to_alias_android(self,
                              str_uids,
                              title,
                              desc,
                              payload,
                              pass_through=0):
        message = PushMessage().restricted_package_name(
            self._app_pkg_name).payload(payload).pass_through(pass_through)
        if pass_through == 0:
            message = message.title(title).description(desc).notify_type(1).extra_element(
                Constants.extra_param_sound_uri, "android.resource://com.xiaomaoqiu.pet/raw/beep")
        recv = self._sender_android.send_to_alias(message.message_dict(), str_uids)
        logging.debug("on send_to_alias_android recv:%s", recv)


    def send_to_alias_ios(self,
                              str_uids,
                              desc,
                              extras):

        logging.info("on send_%s,dict:%s", desc, extras)
        message = PushMessage().description(extras).sound_url(
                                "default").badge(1).category(
                                "action").title("test_title")
        # recv = self._sender1.send_to_alias(message.message_dict_ios(), str_uids)
        recv = self._sender_ios.send_to_alias(message.message_dict_ios(),str_uids)
        logging.debug("on send_to_alias_ios recv:%s", recv)


    def send_to_useraccount_android(self,
                              str_uids,
                              title,
                              desc,
                              payload,
                              pass_through=0):
        message = PushMessage().restricted_package_name(
            self._app_pkg_name).payload(payload).pass_through(pass_through)
        if pass_through == 0:
            message = message.title(title).description(desc)
        recv = self._sender_android.send_to_user_account(message.message_dict(), str_uids)
        logging.debug("on send_to_useraccount_android recv:%s", recv)

    def send_to_useraccount_ios(self,
                              str_uids,
                                payload,
                                extra):
        message = PushMessage().description(payload).sound_url(
            "default").badge(0).category(
            "action").title("test_title").extra(extra)
        # recv = self._sender1.send_to_alias(message.message_dict_ios(), str_uids)
        logging.debug("ios_push_useraccount_message:%s" % message.message_dict_ios())
        recv = self._sender_ios.send_to_user_account(message.message_dict_ios(), str_uids)
        logging.debug("on send_to_alias_ios recv:%s", recv)

    def test_send_to_useraccount_ios(self,
                                str_uids,
                                extras):
        message = PushMessage().description(extras).sound_url(
            "default").badge(1).category(
            "action").title("test_title")
        # recv = self._sender1.send_to_alias(message.message_dict_ios(), str_uids)
        recv = self._sender_ios.send_to_user_account(message.message_dict_ios(), str_uids)
        logging.debug("on send_to_alias_ios recv:%s", recv)
    def test_send_to_alias_ios(self,
                              str_uids,
                              extras):
        dict = json.loads(extras)

        message = PushMessage().description(extras).sound_url(
                                "default").badge(1).category(
                                "action").title("test_title")
        # recv = self._sender1.send_to_alias(message.message_dict_ios(), str_uids)
        recv = self._sender_ios.send_to_alias(message.message_dict_ios(),str_uids)
        logging.debug("on send_to_alias_ios recv:%s", recv)