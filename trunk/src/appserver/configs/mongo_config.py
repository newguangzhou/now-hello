# -*- coding: utf-8 -*-

from lib.mongo_dao_base import MongoMeta


class MongoConfig:
    def __init__(self, *args, **kwargs):
        debug_mode = 0
        if kwargs.has_key("debug_mode"):
            debug_mode = kwargs["debug_mode"]

        # hosts = "192.168.111.169:27018,192.168.111.169:27019,192.168.111.169:27020"
        hosts = "127.0.0.1:27018,127.0.0.1:27019,127.0.0.1:27020"
        #self.default_meta = MongoMeta(hosts="172.19.101.61", port=27017, username="root", passwd="mgdb8w34asdadat51!((")
        self.default_meta = MongoMeta(hosts="120.24.152.121",
                                      port=27020,
                                      username="root",
                                      passwd="mgdb8w34asdadat51!((",
                                      repl_set_name="mongo_shard1")

        if debug_mode != 0:
            #self.default_meta = MongoMeta(hosts=hosts,
            self.default_meta = MongoMeta(hosts="120.24.152.121",
                                          port=27020,
                                          username="root",
                                          passwd="mgdb8w34asdadat51!((",
                                          repl_set_name="mongo_shard1")
        """
        通用数据的mongodb配置
        """
        self.common_mongo_meta = self.default_meta
        """
        用户信息相关的mongodb配置
        """
        self.user_mongo_meta = self.default_meta
        """
        宠物信息相关的mongodb配置
        """
        self.pet_mongo_meta = self.default_meta
        """
        验证信息相关的mongodb配置
        """
        self.auth_mongo_meta = self.default_meta
        """
        全局相关的mongodb配置
        """
        self.global_mongo_meta = self.default_meta
        """
        审核相关的mongodb配置
        """
        self.audit_mongo_meta = self.default_meta
        """
        文件存储相关的mongodb配置
        """
        self.files_mongo_meta = self.default_meta
        """"
         文件存储相关的mongodb配置
        """
        self.op_log_mongo_meta = self.default_meta
