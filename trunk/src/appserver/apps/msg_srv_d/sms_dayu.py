# -*- coding: utf-8 -*-
"""
使用dayu的短信发送服务
"""

import urllib
import logging

import traceback
import json
from top import api
import top

def send_verify(code, product, phones):
    logging.debug("code:%s product:%s phones:%s", code, product, phones)
    req = api.AlibabaAliqinFcSmsNumSendRequest()
    req.set_app_info(top.appinfo("23566149",
                                 "f95d87510975317c9539d858c010f5a0"))
    req.extend = ""
    req.sms_type = "normal"
    req.sms_free_sign_name = "小毛球"
    req.sms_param = "{code:'%s',product:'%s'}" % (code, product)
    req.rec_num = phones
    req.sms_template_code = "SMS_91765057"
    try:
        resp = req.getResponse()
        print resp
        print resp["alibaba_aliqin_fc_sms_num_send_response"]["result"][
            "success"]
        return True
    except Exception, e:
        logging.exception(e)
        return False

def send_message(type,message,phone):
    # logging.debug("code:%s product:%s phones:%s", code, product, phones)
    logging.debug("message:%s,phone:%s",message,phone)
    req = api.AlibabaAliqinFcSmsNumSendRequest()
    req.set_app_info(top.appinfo("23566149",
                                 "f95d87510975317c9539d858c010f5a0"))
    req.extend=""
    req.sms_type="normal"
    req.sms_free_sign_name="小毛球"
    req.rec_num = phone


    if type=="at_home":
        #在家
        req.sms_param = "{name:%s}" % message
        req.sms_template_code = "SMS_91900039"
    elif type=="out_home":
        #离家
        req.sms_param = "{name:%s}" % message
        req.sms_template_code = "SMS_91815049"
    elif type=="low_battery":
        #低电量
        req.sms_param = "{message:%s}" % message
        req.sms_template_code = "SMS_91825060"
    elif type=="superlow_battery":
        #超低电量
        req.sms_param = "{message:%s}" % message
        req.sms_template_code = "SMS_91825060"
    try:
        resp = req.getResponse()
        print resp
        print resp["alibaba_aliqin_fc_sms_num_send_response"]["result"][
            "success"]
        return True
    except Exception, e:
        logging.exception(e)
        return False


def main():
    # send_verify("123222", "小试试", 18666023586)
    send_message("superlow_battery","超低",18825180264)

if __name__ == '__main__':
    main()