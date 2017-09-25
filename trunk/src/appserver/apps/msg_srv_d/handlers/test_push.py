import json
import logging

from tornado import gen
from tornado.web import asynchronous

from lib import error_codes, xmq_web_handler


class PushTest(xmq_web_handler.XMQWebHandler):
      @gen.coroutine
      @asynchronous
      def _deal_request(self):
          logging.debug("OnLogin, %s", self.dump_req())
          self.set_header("Content-Type", "application/json; charset=utf-8")
          res={"status":error_codes.EC_SUCCESS}
          uid=self.get_argument("uid")
          if uid=="":
              res["status"]=error_codes.EC_INVALID_ARGS
          else:
              push_type=self.get_argument("push_type","alias")
              if push_type=="alias":
                  yield self.send_to_alias_ios(uid)
              else:
                  yield self.send_to_useraccount_ios(uid)

          self.res_and_fini(res)

      def send_to_alias_ios(self,uid):
          xiaomi_push2 = self.settings["xiaomi_push2"]
          xiaomi_push2.test_send_to_alias_ios(uid,"test")
      def send_to_useraccount_ios(self,uid):
          xiaomi_push2 = self.settings["xiaomi_push2"]
          xiaomi_push2.test_send_to_useraccount_ios(uid,"test")




      def post(self):
          return self._deal_request()
      def get(self):
          return self._deal_request()