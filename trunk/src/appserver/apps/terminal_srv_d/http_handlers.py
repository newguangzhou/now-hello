# -*- coding: utf-8 -*-
import tornado.web
from tornado import gen
from datetime import datetime
import logging
import urllib
from lib import utils
from lib import error_codes
import json
import base64
from terminal_base import terminal_packets, terminal_commands, terminal_proto
from test_data import TEST_S2C_COMMAND_DATA
logger = logging.getLogger(__name__)
from urllib import quote

JO3_HTML = """
<!DOCTYPE html>
<html>
<script src="http://git.oschina.net/loonhxl/jbase64/raw/master/jbase64.js" language="Javascript"></script>
<script language="Javascript">
function my_post(path, params, method) {
    method = method || "post"; // Set method to post by default if not specified.

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", path);

    for(var key in params) {
        if(params.hasOwnProperty(key)) {
            var hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", key);
            hiddenField.setAttribute("value", params[key]);

            form.appendChild(hiddenField);
         }
    }

    document.body.appendChild(form);
    form.submit();
}
function commit_form(){
	 var imei = document.getElementById("imei").value;
	 var command_content = document.getElementById("command_content").value;
	 var base64 = BASE64.encoder(command_content);//返回编码后的字符 
	 my_post("/send_commandj03",{'imei':imei, 'command_content':base64}) 
}
</script>
<body>
<form id="form_1" >  
<br>
imei:<br>
<input type="text" name="imei" id="imei" size="30">
<br>
j03command:<br>
<input type="text" name="command_content" id="command_content" size="100"><br>
<input type="button" value="Submit" onclick='commit_form()'>
<form>  
</body>
</html>


"""


class SendCommandHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        try:
            imei = self.get_argument("imei")
        except Exception as e:
            self.write("arg error ")
            return

        broadcastor = self.settings["broadcastor"]
        command_pk = terminal_commands.RemotePowerOff()
        pk = terminal_packets.SendCommandReq(imei, command_pk)
        yield broadcastor.send_msg_multicast((imei, ), str(pk))
        logger.info(pk)
        self.write("ok")


class SendCommandHandler2(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        try:
            imei = self.get_argument("imei")
            data = self.get_argument("data")
        except Exception as e:
            self.write("arg error ")
            return
        logger.info("imei:%s, data:%s", imei, data)
        print data
        print quote(data)
        broadcastor = self.settings["broadcastor"]
        #command_pk = terminal_commands.RemotePowerOff()
        #pk = terminal_packets.SendCommandReq(imei, command_pk)

        yield broadcastor.send_msg_multicast((
            "358688000000152",
        ), "[201612101847560003,j03,19,358688000000152@017,20%1%1,3#0,0%15.3%1%202.168.7.5%3000]")
        logger.info(data)
        self.write("ok")


class SendCommandHandler3(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        try:
            imei = self.get_argument("imei")

        except Exception as e:
            self.write("arg error ")
            return
        type = self.get_argument("type", "1")
        command_num = self.get_argument("command_num", "005")
        logger.info("imei:%s, type:%s command_num:%s", imei, type, command_num)
        broadcastor = self.settings["broadcastor"]
        if type == "0":
            command_pk = TEST_S2C_COMMAND_DATA.get(command_num, None)
            print "command_pk", command_pk
            if command_pk is None:
                self.write("arg error ")
                return
            else:
                pk = terminal_packets.SendCommandReq(imei, command_pk)
        else:
            pk = terminal_packets.GetLocationAck(terminal_proto.GenSN(), imei)
        send_data = str(pk)
        ret = yield broadcastor.send_msg_multicast((imei, ), send_data)
        ret_str = "send ok" if ret else "send fail"
        self._OnOpLog("s2c send_data:%s ret:%s" % (send_data, ret_str), imei)
        self.write(ret_str)
        unreply_msg_mgr = self.settings["unreply_msg_mgr"]
        unreply_msg_mgr.add_unreply_msg(pk.sn, imei, send_data, command_num)

    def _OnOpLog(self, content, imei):
        logger.info("content:%s imei:%s", content, imei)
        op_log_dao = self.settings["op_log_dao"]
        op_log_dao.add_op_info(imei=unicode(imei), content=unicode(content))


class SendCommandHandler4(tornado.web.RequestHandler):
    @gen.coroutine
    def do_request(self):
        try:
            imei = self.get_argument("imei")
            content = self.get_argument("content", "test")
        except Exception as e:
            self.write("arg error ")
            return
        broadcastor = self.settings["broadcastor"]
        print imei, content
        ret = yield broadcastor.send_msg_multicast((imei, ), str(content))
        ret_str = "send ok" if ret else "send fail"
        self._OnOpLog("s2c send_data:%s ret:%s" % (content, ret_str), imei)
        self.write(ret_str)

    def get(self):
        return self.do_request()

    def post(self):
        return self.do_request()

    def _OnOpLog(self, content, imei):
        logger.info("content:%s imei:%s", content, imei)
        op_log_dao = self.settings["op_log_dao"]
        op_log_dao.add_op_info(imei=unicode(imei), content=unicode(content))


class SendParamsCommandHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def do_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        try:
            imei = self.get_argument("imei")
            content = self.get_argument("command_content")
        except Exception as e:
            res["status"] = error_codes.EC_INVALID_ARGS
        else:
            broadcastor = self.settings["broadcastor"]
            pk = terminal_packets.SendCommandReq(imei, content)
            send_data = str(pk)
            ret = yield broadcastor.send_msg_multicast((imei, ), send_data)
            if ret:
                ret_str = "send ok"
            else:
                ret_str = "send fail"
                res["status"] = error_codes.EC_SEND_CMD_FAIL
            self._OnOpLog("s2c send_data:%s ret:%s" % (send_data, ret_str),
                          imei)
            unreply_msg_mgr = self.settings["unreply_msg_mgr"]
            msg_type = content[0:3]
            unreply_msg_mgr.add_unreply_msg(pk.sn, imei, send_data, msg_type)
        data = json.dumps(res, ensure_ascii=False, encoding='utf8')
        self.write(data)

    def get(self):
        return self.do_request()

    def post(self):
        return self.do_request()

    def _OnOpLog(self, content, imei):
        logger.info("content:%s imei:%s", content, imei)
        op_log_dao = self.settings["op_log_dao"]
        op_log_dao.add_op_info(imei=unicode(imei), content=unicode(content))


class SendCommandHandlerJ13(tornado.web.RequestHandler):
    @gen.coroutine
    def do_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        try:
            imei = self.get_argument("imei")
        except Exception as e:
            res["status"] = error_codes.EC_INVALID_ARGS
        else:
            broadcastor = self.settings["broadcastor"]
            pk = terminal_packets.GetLocationAck(terminal_proto.GenSN(), imei)
            send_data = str(pk)
            ret = yield broadcastor.send_msg_multicast((imei, ), send_data)
            #ret_str = "send ok" if ret else "send fail"
            if ret:
                ret_str = "send ok"
            else:
                ret_str = "send fail"
                res["status"] = error_codes.EC_SEND_CMD_FAIL
            self._OnOpLog("s2c send_data:%s ret:%s" % (send_data, ret_str),
                          imei)
        data = json.dumps(res, ensure_ascii=False, encoding='utf8')
        self.write(data)

    def get(self):
        return self.do_request()

    def post(self):
        return self.do_request()

    def _OnOpLog(self, content, imei):
        logger.info("content:%s imei:%s", content, imei)
        op_log_dao = self.settings["op_log_dao"]
        op_log_dao.add_op_info(imei=unicode(imei), content=unicode(content))


class SendCommandHandlerJ03(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        self.write(JO3_HTML)

    @gen.coroutine
    def post(self):

        try:
            imei = self.get_argument("imei")
            content = self.get_argument("command_content")
        except Exception as e:
            self.write("arg error ")
            return
        content = base64.decodestring(content)
        logger.info("content :%s", content)
        broadcastor = self.settings["broadcastor"]
        pk = terminal_packets.SendCommandReq(imei, content)
        send_data = str(pk)
        #send_data = send_data.replace("*", "#")
        ret = yield broadcastor.send_msg_multicast((imei, ), send_data)
        ret_str = "send ok" if ret else "send fail"
        self._OnOpLog("s2c send_data:%s ret:%s" % (send_data, ret_str), imei)
        self.write(ret_str)
        unreply_msg_mgr = self.settings["unreply_msg_mgr"]
        msg_type = content[0:3]
        unreply_msg_mgr.add_unreply_msg(pk.sn, imei, send_data, msg_type)

    def _OnOpLog(self, content, imei):
        logger.info("content:%s imei:%s", content, imei)
        op_log_dao = self.settings["op_log_dao"]
        op_log_dao.add_op_info(imei=unicode(imei), content=unicode(content))


class GetOpLogHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        op_log_dao = self.settings["op_log_dao"]
        #ret = {}
        start_time = None
        end_time = None
        try:
            imei = self.get_argument("imei")
            start = self.get_argument("start")
            end = self.get_argument("end", None)
            start_time = utils.str2datetime(start, "%Y-%m-%d %H:%M:%S")
            if end is not None:
                end_time = utils.str2datetime(end, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            self.write("arg error ")
            return

        op_ret = yield op_log_dao.get_log_info(start_time, end_time, imei,
                                               ("imei", "content", "log_time"))
        ret = "<html>"
        for item in op_ret:
            ret += " 【log_time】:%s 【imei】:%s 【content】:%s <br><br>" % (
                utils.date2str(item["log_time"]), item["imei"],
                item["content"])
            #ret
        ret += "</html>"
        self.write(ret)