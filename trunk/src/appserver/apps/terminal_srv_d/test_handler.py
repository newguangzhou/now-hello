# -*- coding:utf-8 -*-
import tornado.web
from lib import error_codes
class CloseTcp(tornado.web.RequestHandler):

    def _deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        try:
            imei = self.get_argument("imei")
        except Exception as e:
            res["status"] = error_codes.EC_INVALID_ARGS
            return
        broadcastor = self.settings["broadcastor"]
        conn_mgr=self.settings["conn_mgr"]

        connid=broadcastor.get_connid_by_imei(imei)
        if connid is None:
            res={"status":"socket不在线"}
            self.write(res)
            return
        del broadcastor._imei_conn_dict[imei]
        del broadcastor._conn_imei_dict[connid]
        conn=conn_mgr.GetConn(connid)
        if conn is not None:
            conn.close
            del conn_mgr._conns[connid]
            res={"status":"成功关闭"}
        self.write(res)


    def post(self):
        self._deal_request()

    def get(self):
        self._deal_request()
