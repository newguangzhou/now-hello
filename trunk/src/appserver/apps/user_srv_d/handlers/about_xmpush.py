# -*- coding: utf-8 -*-
from helper_handler import HelperHandler


# 设置alias
class SetAliasHandler(HelperHandler):
    def _deal_request(self):
        self.set_header("Content-Type", "application/json; charset=utf-8")




    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()


# 注销alias
class UnSetAliasHandler(HelperHandler):
    def _deal_request(self):
        self.set_header("Content-Type", "application/json; charset=utf-8")

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()


 # 设置account
class SetAccountHandler(HelperHandler):
    def _deal_request(self):
        self.set_header("Content-Type", "application/json; charset=utf-8")

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()


# 注销account
class UnSetAccountHandler(HelperHandler):
    def _deal_request(self):
        self.set_header("Content-Type", "application/json; charset=utf-8")

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()