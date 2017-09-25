# -*- coding: utf-8 -*-

import copy
import datetime

import pymongo
from pymongo.operations import IndexModel

FILES_DATABASE = "xmq_files"
"""
用户logo图片存储表
"""
USER_LOGOS_TB = "user_logos"
"""
对外发布的文件
"""
PUBLIC_FILES_TB = "public_files"
