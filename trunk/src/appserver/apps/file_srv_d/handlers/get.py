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

from helper_handler import HelperHandler

class Get(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnGet, %s", self.dump_req())
        
        files_dao = self.settings["files_dao"]
        conf = self.settings["appconfig"]
        
        # 获取请求参数
        type = None
        file_id = None
        try:
            type = int(self.get_argument("type"))
            if not files_dao.is_valid_category(type):
                self.arg_error("type")
            file_id = self.get_argument("file_id")
        except Exception,e:
            logging.warning("OnGet, invalid args, %s %s", self.dump_req(), self.dump_exp(e))
            self.send_error(500)
            return
        
        # 
        try:
            file = yield files_dao.get_file(type, file_id)
            
            if not file:
                logging.warning("OnGet, not found, %s", self.dump_req())
                self.send_error(404)
                return
            
            self.set_header("Content-Type", files_dao.get_content_type(type))
            self.set_header("Content-Disposition", "attachment;filename=%s" % (file.filename,))
            
            while True:
                data = yield files_dao.read_file(file, 2048)
                if not data:
                    break
                self.write(data)
            self.finish()
            logging.debug("OnGet, success, %s", self.dump_req())
        except Exception,e:
            logging.warning("OnGet, error, %s %s", self.dump_req(), self.dump_exp(e))
            self.send_error(500)
            return 
        
    def post(self):
        return self._deal_request()
    
    def get(self):
        return self._deal_request()
    
    