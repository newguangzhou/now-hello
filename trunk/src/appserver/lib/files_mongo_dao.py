# -*- coding: utf-8 -*-

import threading
import logging 
import time
import traceback
import random
import json
import io
import bson

from tornado import ioloop, gen

import files_mongo_defines as files_def
import utils
import type_defines

import gridfs

from PIL import Image 
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

from mongo_dao_base import MongoDAOBase

_FILE_CATEGORY_TB_MAP = {
    type_defines.USER_LOGO_FILE:files_def.USER_LOGOS_TB,
    type_defines.PUBLIC_FILE:files_def.PUBLIC_FILES_TB,
    }

class FilesMongoDAOException(Exception):
    def __init__(self, message, *args):
        self._msg = message % tuple(args)
        
    def __str__(self):
        return self._msg

class FilesMongoDAO(MongoDAOBase):
    def __init__(self, *args, **kwargs):
        MongoDAOBase.__init__(self, *args, **kwargs)
    
    def on_thread_init(self, th_local):
        if not hasattr(th_local, "gridfs_insts"):
            th_local.gridfs_insts = {}
            for (k,v) in _FILE_CATEGORY_TB_MAP.items():
                db = th_local.mongo_client[files_def.FILES_DATABASE]
                th_local.gridfs_insts[k] = gridfs.GridFS(db, v)
    
    def _get_file_gridfs(self, file_category):
        if not _FILE_CATEGORY_TB_MAP.has_key(file_category):
            raise FilesMongoDAOException("Unknown file category \"%u\"", file_category)
        th_local = self.get_thread_local()
        return th_local.gridfs_insts[file_category]
    
    def _resize_image(self, fp, width, heigth):
        imgobj = Image.open(fp)
        imgobj = imgobj.resize((width, heigth), Image.ANTIALIAS)
        
        if imgobj.mode == "P":
            imgobj = imgobj.convert("RGB")
        
        savefp = io.BytesIO()
        imgobj.save(savefp, "jpeg")
        
        return savefp.getvalue()
    
    def is_valid_category(self, category):
        return _FILE_CATEGORY_TB_MAP.has_key(category)
    
    def get_content_type(self, category):
        if category == type_defines.PUBLIC_FILE:
            return "application/octet-stream"
        else:
            return "image/jpeg"
    
    @gen.coroutine
    def upload_file(self, file_category, fp, filename, **kwargs):
        file_id = None
        if kwargs.has_key("_id"):
            file_id = bson.objectid.ObjectId(kwargs["_id"])
        
        up_extras = kwargs
        
        def _callback(mongo_client, **kwargs):
            fs = self._get_file_gridfs(file_category)
            
            chunk_size = 1024 * 1024
            if kwargs.has_key("chunk_size"):
                chunk_size = kwargs["chunk_size"]
            
            file_args = {"filename":filename, "chunkSize":chunk_size}
            if file_id:
                file_args["_id"] = file_id
            
            ret = None
            if up_extras.has_key("width"):
                data = self._resize_image(fp, up_extras["width"], up_extras["height"])
                ret = fs.put(data, **file_args)
            else:
                fin = fs.new_file(**file_args)
                ret = fin._id
                fin.write(fp)
                fin.close()
                
            # 删除旧版本文件
            for file in fs.find({"filename":filename, "_id":{"$ne":ret}}):
                fs.delete(file._id)
            
            return str(ret)
        
        ret = yield self.submit(_callback)
        raise gen.Return(ret)
    
    @gen.coroutine
    def get_file(self, file_category, file_id):
        def _callback(mongo_client, **kwargs):
            fs = self._get_file_gridfs(file_category)
            _id = bson.objectid.ObjectId(file_id)
            if not fs.exists(_id):
                return None
            return fs.get(_id)
        ret = yield self.submit(_callback)
        raise gen.Return(ret)
    
    @gen.coroutine
    def read_file(self, fp, size = -1):
        def _callback(mongo_client, **kwargs):
            return fp.read(size)
        ret = yield self.submit(_callback)
        raise gen.Return(ret)
    
    @gen.coroutine
    def delete_file(self, file_category, file_id):
        def _callback(mongo_client, **kwargs):
            fs = self._get_file_gridfs(file_category)
            id = bson.objectid.ObjectId(file_id)
            fs.delete(id)
        yield self.submit(_callback)
        
    
        
            
            
    
