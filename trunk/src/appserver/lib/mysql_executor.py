# -*- coding: utf-8 -*-

import sys
import datetime 
import time

from tornado.concurrent import Future 
from tornado import gen

import utils

class MySQLExecutorException(Exception):
    def __init__(self, message):
        self._message = message  
    
    def __str__(self):
        return self._message 

SELECT_SQL = 0
INSERT_SQL = 1 
UPDATE_SQL = 2 
DELETE_SQL = 3

class MySQLExecutor:
    def __init__(self, *args, **kwargs):
        self._mysql_inst_mgr = None
        self._get_inst_functor = None
        
        self._mysql_inst_mgr = kwargs["mysql_inst_mgr"]
    
    def get_mysql_inst_mgr(self):
        return self._mysql_inst_mgr
    
    def get_mysql_inst(self, **kwargs):     
        ret = self._mysql_inst_mgr.get_inst()
        if not ret:
            raise MySQLExecutorException("Get mysql db inst error")
        return ret
    
    @gen.coroutine
    def _async_select(self, sql, vals, inst = None, **kwargs):
        ret = []
        max_id = 0
        key_set = set()
        auto_convert = False 
        account_max_id = False
        mk_timestamp = False
        set_key = None
        if kwargs.has_key("auto_convert"):
            auto_convert = kwargs["auto_convert"]
        if kwargs.has_key("account_max_id"):
            account_max_id = kwargs["account_max_id"]
        if kwargs.has_key("mk_timestamp"):
            mk_timestamp = kwargs["mk_timestamp"]
        if kwargs.has_key("set_key"):
            set_key = kwargs["set_key"]
        
        if not vals:
            vals = None 
        
        if not inst: 
            inst = self.get_mysql_inst(**kwargs)
        cursor = yield inst.execute(sql, vals) 
        for row in cursor:
            tmp = {}
            for i in range(0, len(row)):
                colval = row[i]
                if auto_convert:
                    if isinstance(colval, datetime.date)  or isinstance(colval, datetime.datetime):
                        if mk_timestamp:
                            colval = utils.date2int(colval)
                        else:
                            colval = utils.date2str(colval)
                    elif isinstance(colval, float):
                        colval = str(colval)
                tmp[cursor.description[i][0]] = colval
                if account_max_id and cursor.description[i][0] == "id" and colval > max_id:
                    max_id = colval
                if set_key and cursor.description[i][0] == set_key:
                    key_set.add(colval)
                        
            ret.append(tmp)
        
        tmp_ret = [ret]
        if account_max_id:
            tmp_ret.append(max_id)
        if set_key:
            tmp_ret.append(key_set)
        if len(tmp_ret) > 1:
            raise gen.Return(tuple(tmp_ret))
        else:
            raise gen.Return(tmp_ret[0])
    
    @gen.coroutine
    def _async_delete(self, sql, vals, inst = None, **kwargs):
        ret = None
        
        if not vals:
            vals = None 
        
        if not inst: 
            inst = self.get_mysql_inst(**kwargs)
        cursor = yield inst.execute(sql, vals)
        ret = cursor.rowcount
        raise gen.Return(ret)
    
    @gen.coroutine 
    def _async_update(self, sql, vals, inst = None, **kwargs):
        ret = None 
        if not vals:
            vals = None
        if not inst: 
            inst = self.get_mysql_inst(**kwargs)
        cursor = yield inst.execute(sql, vals)
        ret = cursor.rowcount
        raise gen.Return(ret)
        
    @gen.coroutine
    def _async_insert(self, sql, vals, inst = None, **kwargs):
        ret = None 
        if not vals:
            vals = None
            
        if not inst: 
            inst = self.get_mysql_inst(**kwargs)
        cursor = yield inst.execute(sql, vals)
        ret = cursor.lastrowid
        raise gen.Return(ret)
    
    @gen.coroutine
    def batch_execute(self, sql_and_vals, inst = None, **kwargs):
        ret = []
        rollback = False
        if not inst:
            inst = self.get_mysql_inst(**kwargs)
        trans = yield inst.begin()
            
        for v in sql_and_vals:
            sql = v[0]
            vals = v[1]
                
            if not vals:
                vals = None 
                
            try:
                cursor = yield trans.execute(sql, vals)
                rollback = True
                n = cursor.rowcount
                ret.append(n)
                cursor.close()
                if not n: # 更新操作失败则需要回滚
                    raise MySQLExecutorException("Execute sql failed when doing transaction, sql=\'%s\' vals=\'%s\'" % (sql, str(vals)))
            except Exception,e:
                if rollback: 
                    yield trans.rollback()
                    raise e
        yield trans.commit()
        raise gen.Return(ret)
    
    @gen.coroutine
    def execute(self, sql, sql_type, vals, inst = None, **kwargs):
        assert(sql_type == SELECT_SQL or sql_type == INSERT_SQL 
               or sql_type == UPDATE_SQL or sql_type == DELETE_SQL)
        
        if not vals:
            vals = None
        
        ret = None
        if sql_type == SELECT_SQL:
            ret = yield self._async_select(sql, vals, inst, **kwargs)
        elif sql_type == INSERT_SQL:
            ret = yield self._async_delete(sql, vals, inst, **kwargs)
        elif sql_type == UPDATE_SQL:
            ret = yield self._async_update(sql, vals, inst, **kwargs)
        else:
            ret = yield self._async_insert(sql, vals, inst, **kwargs)
        
        raise gen.Return(ret)
    
