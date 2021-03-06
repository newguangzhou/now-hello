# -*- coding: utf-8 -*-

from tornado import gen

from files_mongo_dao import FilesMongoDAO

class FilesDAO:
    @staticmethod
    def new(**kwargs):
        mongo_meta = kwargs["mongo_meta"]
        mongo_dao = FilesMongoDAO(meta = mongo_meta)
        inst = FilesDAO(db_dao = mongo_dao)
        return inst
    
    def __init__(self, **kwargs):
        self._db_dao = kwargs["db_dao"]
    
    def __getattr__(self, attr):
        return getattr(self._db_dao, attr)
        
