# -*- coding: utf-8 -*-

# ##############################################
# # 审计相关定义
# ##############################################
# """
# 有效的审计状态定义
# """
# VALID_AUDIT_STATES = set([
#     0,  # 未审核
#     1,  # 审核未通过
#     2,  # 审核通过
# ])
# """"
# 有效的审计类型定义
# """
# VALID_AUDIT_TYPES = set([])

##############################################
# 认证相关定义
##############################################
"""
用户认证类型
"""
USER_AUTH = 1
"""
正常用户认证
"""
NORMAL_AUTH = 1
"""
老用户认证
"""
OLD_AUTH = 2
"""
老用户新认证
"""
OLD_NORMAL_AUTH = 3
"""
用户认证状态正常
"""
ST_AUTH_NORMAL = 1
"""
用户认证状态被永久冻结
"""
ST_AUTH_FREEZE_FOREVER = 2
"""
用户认证状态被暂时冻结
"""
ST_AUTH_FREEZE_TEMP = 3
"""
验证码类型
"""
VERIFY_CODE_TYPES = set([
    1,  # 注册验证码
    2,  # 登录验证码
    3,  # 密码找回验证码
])

##############################################
# 全局ID分配相关定义
##############################################
USER_GID = 2

AUDIT_GID = 6

PET_GID = 7

###############################################
# 文件种类定义
###############################################
USER_LOGO_FILE = 1

PUBLIC_FILE = 50
################################################
# 设备类型
################################################
DEVICE_ANDROID = 1
DEVICE_IOS = 2





HTTP_HD_OS = "X-OS"
#android系统版本号,默认23
HTTP_HD_OS_INT="x_os_int"
HTTP_HD_APPVERSION = "X-App-Version"
# HTTP_HD_DEVICE_MODEL = "X-OS-Name"
HTTP_HD_DEVICE_MODEL = "device_model"
HTTP_HD_ANDROID_START_STRING = "Android"
PLATFORM_ANDROID = 1
PLATFORM_IOS = 2
