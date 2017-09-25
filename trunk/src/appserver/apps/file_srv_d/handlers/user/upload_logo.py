# -*- coding: utf-8 -*-

import tornado.web
import json
import hashlib
import random 
import time
import io

import logging
import traceback

from tornado.web import asynchronous
from tornado import gen

from lib import error_codes
from lib import type_defines
from lib import sys_config
from lib.sys_config import SysConfig
from lib import type_defines

from handlers.helper_handler import HelperHandler

class UploadLogo(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnUploadLogo, %s", self.dump_req())
        
        self.set_header("Content-Type", "application/json; charset=utf-8")
        
        res = {"status":error_codes.EC_SUCCESS}
        files_dao = self.settings["files_dao"]
        user_dao = self.settings["user_dao"]
        conf = self.settings["appconfig"]
        
        # 获取请求参数
        uid = None 
        token = None
        file = None
        try:
            req = self.request
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            
            if len(req.files) <= 0:
                self.arg_error("Upload file not found")
            if len(req.files) != 1:
                self.arg_error("Upload file count is more than one")
            if len(req.files.values()[0]) != 1:
                self.arg_error("Upload file count is more than one")
            file = req.files.values()[0][0]
        except Exception,e:
            logging.warning("OnUploadLogo, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return 
        
        # 
        try:    
            # 检查账号状态
            st = yield self.check_account_status("OnUploadLogo check account", res, type_defines.USER_AUTH, uid)
            if not st:
                return
            
            # 检查token
            st = yield self.check_token("OnUploadLogo", res, type_defines.USER_AUTH, uid, token)
            if not st:
                return
            
            # 检查文件类型
            fname = file["filename"].lower()
            extname = None
            for type in SysConfig.current().get(sys_config.SC_UPLOAD_IMAGE_TYPES):
                if fname.endswith(type):
                    extname = type
                    break
            if not extname:
                logging.warning("OnUploadLogo, not support file type, filename=%s %s", fname, self.dump_req())
                res["status"] = error_codes.EC_INVALID_FILE_TYPE
                self.res_and_fini(res)
                return
            
            # 检查文件大小
            if len(file["body"]) > SysConfig.current().get(sys_config.SC_USER_LOGO_MAX_SIZE):
                logging.warning("OnUploadLogo, file size limit, %s", self.dump_req())
                res["status"] = error_codes.EC_FILE_SIZE_LIMIT
                self.res_and_fini(res)
            
            # 重命名
            rename = "%u_logo%s" % (uid, extname)
            
            # 保存文件
            fp = io.BytesIO(file["body"])
            file_id = yield files_dao.upload_file(type_defines.USER_LOGO_FILE, fp, rename)
            
            # 更新用户信息
            #user_dao.update_user_info(uid, logo_url = file_id)
            
            # 上传成功
            logging.debug("OnUploadLogo, success, orig_name=%s rename=%s %s", fname, rename, self.dump_req())
            res["file_url"] = SysConfig.current().gen_file_url(type_defines.USER_LOGO_FILE, file_id)
            
            self.res_and_fini(res)
        except Exception,e:
            logging.warning("OnUploadLogo, error, %s %s", self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR 
            self.res_and_fini(res)
            return 
        
    def post(self):
        return self._deal_request()
    
    def get(self):
        self.write('''
        <html>
          <head><title>Upload File</title></head>
          <body>
            <form action='upload_logo' enctype="multipart/form-data" method='post'>
            uid:<input type="text" name="uid"/></br/>
            token:<input type="text" name="token"/></br>
            file:<input type='file' name='file'/><br/>
            <input type='submit' value='submit'/>
            </form>
          </body>
        </html>
        ''')
    
    