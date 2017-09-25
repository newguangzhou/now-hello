""" 
@biref log util
@file logger.py
@author ChenYongqiang
@date 2014-12-04
    
YY Inc Copyright (c) 2005-2014  yy.com
"""


import logging
import os
import inspect

_logger = None

def _LogAdp(log_func_name, msg):
    stack = inspect.stack()
    frame = stack[2][0]
    
    frame_info = inspect.getframeinfo(frame)
    extra = {"bt_filename":frame_info[0], "bt_lineno":frame_info[1], "bt_func":frame_info[2]}
    
    adp = logging.LoggerAdapter(_logger, extra)
    logging.LoggerAdapter.__dict__[log_func_name](adp, msg)
    
def debug(format, *args):
    _LogAdp("debug", format % tuple(args))

def info(format, *args):
    _LogAdp("info", format % tuple(args))

def warning(format, *args):
    _LogAdp("warning", format % tuple(args))

def error(format, *args):
    _LogAdp("error", format % tuple(args))
    
def Init(dir, console_out = False, category = "guess_server", write_file = True):
    global _logger
    
    _logger = logging.getLogger(category)
    
    _logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(bt_filename)s:%(bt_lineno)d")
    
    fh = None
    if write_file:
        file_path = dir
        if not file_path.endswith("/"):
            file_path += "/"
    
        assert not os.path.isfile(file_path)
    
        if not os.path.isdir(file_path):
            os.makedirs(file_path)
    
        file_path += "%s.log" % (category,)
    
        fh = logging.FileHandler(file_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        
    ch = None
    if console_out:
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
    
        ch.setFormatter(formatter)
    
    if fh:
        _logger.addHandler(fh)
    if ch:
        _logger.addHandler(ch)
    
