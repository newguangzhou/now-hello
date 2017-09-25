# -*- coding: utf-8 -*-

import traceback
import struct
import StringIO
import time
import datetime
import pdb
from test_data import TEST_S2C_COMMAND_DATA
import logging
from tornado import gen
from terminal_base import terminal_proto, terminal_commands, terminal_packets, util
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from get_location import get_location_by_wifi, get_location_by_bts_info, get_location_by_mixed, convert_coordinate

_TERMINAL_CONN_MAX_BUFFER_SIZE = 2 * 1024 * 1024  # 2M
logger = logging.getLogger(__name__)

from lib import utils
from lib import push_msg

LOW_BATTERY = 25
ULTRA_LOW_BATTERY = 15


class TerminalHandler:
    executor = ThreadPoolExecutor(5)

    def __init__(self, *args, **kwargs):
        if len(args) > 0:
            self.conn_mgr = args[0]
        else:
            self.conn_mgr = kwargs["conn_mgr"]

        self.debug = False
        if len(args) > 1:
            self.debug = args[1]
        elif kwargs.has_key("debug"):
            self.debug = kwargs["debug"]

        self.imei_timer_mgr = kwargs.get("imei_timer_mgr", None)
        if self.imei_timer_mgr is None:
            if len(args) > 2:
                self.imei_timer_mgr = args[2]

        self._broadcastor = kwargs.get("broadcastor", None)
        if self._broadcastor is None:
            if len(args) > 3:
                self._broadcastor = args[3]

        self.op_log_dao = kwargs.get("op_log_dao", None)
        self.new_device_dao = kwargs.get("new_device_dao", None)
        self.pet_dao = kwargs.get("pet_dao", None)
        self.msg_rpc = kwargs.get("msg_rpc", None)
        self.unreply_msg_mgr = kwargs.get("unreply_msg_mgr", None)

        # self.terminal_proto_ios = {}

        self.terminal_proto_guarder = {}

    def OnOpen(self, conn_id):
        conn = self.conn_mgr.GetConn(conn_id)
        logger.info("Terminal conn is opened, id=%u peer=%s", conn_id,
                    conn.GetPeer())
        proto_io = terminal_proto.ProtoIO()
        self.terminal_proto_guarder[conn_id] = terminal_proto.ProtoIoGuarder(
            proto_io)
        return True

    @gen.coroutine
    def OnData(self, conn_id, data):
        conn = self.conn_mgr.GetConn(conn_id)

        logger.debug("onData conn_id:%d data:%s hex_data:%s ", conn_id, data,
                     data.encode('hex'))
        guarder = self.terminal_proto_guarder.get(conn_id, None)
        if guarder is None:
            return
        proto_io = yield guarder.get()

        # Check buffer
        if proto_io.read_buff.GetSize() + len(
                data) >= _TERMINAL_CONN_MAX_BUFFER_SIZE:
            logger.error(
                "Terminal conn read buffer is overflow, id=%u peer=%s",
                conn_id, conn.GetPeer())
            conn.close()
            return
            # Write to buffer
        proto_io.read_buff.AppendData2(data)
        # logger.debug("dump1:%s", proto_io.read_buff.Dump())
        # Read packets
        try:
            while True:
                header, body = proto_io.Read()
                if header == terminal_proto.ERROR_START:
                    imei = self._broadcastor.get_imei_by_conn(conn_id)
                    logging.debug("error_start,imei:%s",imei)
                    continue
                if header is None:
                    break
                if header == terminal_proto.SIMPLE_HEART:
                    imei = self._broadcastor.get_imei_by_conn(conn_id)
                    logger.info(
                        "Receive a terminal packet simple heart id=%u peer=%s imei=%s",
                        conn_id, conn.GetPeer(), imei)
                    if imei is not None:
                        self._OnOpLog("[]", imei)
                        self.imei_timer_mgr.add_imei(imei)
                    continue
                logger.info(
                    "Receive a terminal packet, header=\"%s\" body=\"%s\" id=%u peer=%s",
                    str(header), body, conn_id, conn.GetPeer())

                # Dispatch
                disp_status = True
                if header.directive == "J01":  # 上传位置
                    disp_status = yield self._OnReportLocationInfoReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J02":  # 上传健康信息
                    disp_status = yield self._OnReportHealthInfoReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "R03":  # 发送远程命令设备回应的ack
                    disp_status = yield self._OnSendCommandAck(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J12":  # 设备发送的心跳请求
                    disp_status = yield self._OnHeartbeatReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J17":  # 设备上传状态数据F
                    disp_status = yield self._OnReportTerminalStatusReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J18":  # 设备上传日志数据
                    disp_status = yield self._OnUploadTerminalLogReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J04":
                    disp_status = yield self._OnSyncCommandReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J16":
                    disp_status = yield self._OnUploadStationLocationReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J15":
                    disp_status = yield self._OnGpsSwitchReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "R13":
                    disp_status = yield self._OnReportLocationInfoReq(
                        conn_id, header, body, conn.GetPeer(), False)
                else:
                    logger.warning(
                        "Unknown directive, directive=\"%s\" id=%u peer=%s",
                        header.directive, conn_id, conn.GetPeer())

                if not disp_status:
                    conn.close()
                    # 设备离线消息

                    return
        except Exception, e:
            logger.exception("id=%u peer=%s,Exception:%s", conn_id,
                             conn.GetPeer(), e)
            conn.close()
            return

        guarder.release()
        return

    def OnError(self, conn_id, errno):
        logger.warning("Terminal conn has an error, id=%u errno=%u peer=%s",
                       conn_id, errno,
                       self.conn_mgr.GetConn(conn_id).GetPeer())

    def OnClose(self, conn_id, is_eof):
        conn = self.conn_mgr.GetConn(conn_id)
        if is_eof:
            logger.warning("Terminal conn is closed by peer, peer=\"%s\"",
                           conn.GetPeer())
        else:
            logger.warning("Terminal conn is closed, info=\"%s\"",
                           conn.GetPeer())

        if self.terminal_proto_guarder.has_key(conn_id):
            del self.terminal_proto_guarder[conn_id]
        conn.close()
        # 打日志
        imei = self._broadcastor.get_imei_by_conn(conn_id)

        self._broadcastor.un_register_conn(conn_id)

    def OnTimeout(self, conn_id):
        pass

    def _OnOpLog(self, content, imei):
        self.op_log_dao.add_op_info(imei=unicode(imei),
                                    content=unicode(content))

    @gen.coroutine
    def _send_res(self, conn_id, ack, imei, peer):
        str_ack = str(ack)
        ret = yield self.conn_mgr.Send(conn_id, str_ack)
        self._OnOpLog("s2c send_data:%s peer:%s ret:%s" %
                      (ack.orgin_data(), peer, str(ret)), imei)
        raise gen.Return(ret)

    @gen.coroutine
    def _OnReportLocationInfoReq(self,
                                 conn_id,
                                 header,
                                 body,
                                 peer,
                                 need_send_ack=True):
        # Parse packet
        pk = terminal_packets.ReportLocationInfoReq()
        pk.Parse(body)

        # 电量突然跳零的处理
        electric_quantity = (int)(pk.electric_quantity)
        device_info_electric_quantity = yield self.new_device_dao.get_device_info(pk.imei, ("electric_quantity",))
        if (int)(device_info_electric_quantity.get("electric_quantity", 0)) - (int)(electric_quantity) > 10 and (int)(
                device_info_electric_quantity.get("electric_quantity", 0)) - (int)(electric_quantity) < 100:
            electric_quantity = (int)(device_info_electric_quantity.get("electric_quantity", 0)) - 5
        elif (int)(device_info_electric_quantity.get("electric_quantity", 0)) - (int)(electric_quantity) > 10 and device_info_electric_quantity.get("electric_quantity", 0)==200:
            electric_quantity=100
        # 电量突然跳零的处理
        pk.electric_quantity = electric_quantity

        pet_info = yield self.pet_dao.get_pet_info(
            ("pet_id", "uid", "home_wifi", "common_wifi", "target_energy"),
            device_imei=pk.imei)

        now_calorie = pk.calorie
        if pet_info is not None:
            # 卡路里重启调零的处理
            # sn_end_num = int(header.sn[-4:])
            # if sn_end_num <= 3:
            temp_diary = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
            res_info =yield self.pet_dao.get_sport_info(pet_info["pet_id"], temp_diary, datetime.datetime.now())
            if res_info is not None and res_info.count()>0:
                    if res_info[0].get("calorie", 0) > now_calorie:
                        now_calorie = res_info[0].get("calorie", 0)
        pk.calorie = now_calorie
        # 卡路里突然调零的处理

        str_pk = str(pk)

        logger.debug(
            "OnReportLocationInfoReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        self._OnOpLog('c2s header=%s pk=%s peer=%s' % (header, str_pk, peer),
                      pk.imei)

        self.updateDeviceStatus(pk.imei)
        if need_send_ack:
            ack = terminal_packets.ReportLocationInfoAck(header.sn)
            yield self._send_res(conn_id, ack, pk.imei, peer)
        locator_time = pk.location_info.locator_time
        locator_status = pk.location_info.locator_status
        lnglat = []
        lnglat2 = []
        lnglat3 = []
        radius = -1
        radius2 = -1
        radius3 = -1

        if pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_GPS:

            ret = convert_coordinate((float(pk.location_info.longitude),
                                      float(pk.location_info.latitude)), "gps")
            if ret is not None:
                lnglat = [ret[0], ret[1]]

        elif pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_STATION:
            bts_info, near_bts_infos = util.split_locator_station_info(
                pk.location_info.station_locator_data)
            ret = yield self.get_location_by_bts_info(pk.imei, bts_info,
                                                      near_bts_infos)
            if ret is not None:
                lnglat = [ret[0], ret[1]]
                radius = ret[2]
        elif pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_MIXED:
            bts_info, near_bts_infos = util.split_locator_station_info(
                pk.location_info.station_locator_data)

            ret = yield self.get_location_by_mixed(
                pk.imei, bts_info, near_bts_infos, pk.location_info.mac)

            if ret is not None:
                lnglat = [ret[0], ret[1]]
                radius = ret[2]

            ret2 = yield self.get_location_by_wifi(pk.imei,
                                                   pk.location_info.mac)
            if ret2 is not None:
                lnglat2 = [ret2[0], ret2[1]]
                radius2 = ret2[2]

            ret3 = yield self.get_location_by_bts_info(pk.imei, bts_info,
                                                       near_bts_infos)
            if ret3 is not None:
                lnglat3 = [ret3[0], ret3[1]]
                radius3 = ret3[2]

        else:
            logger.warning("imei:%s location fail", pk.imei)

        if pet_info is None:
            logger.error("imei:%s pk:%s not found pet_info", pk, str_pk)
        time_stamp = int(time.time())
        if len(lnglat) != 0:
            location_info = {"lnglat": lnglat,
                             "radius": radius,
                             "locator_time": locator_time,
                             "locator_status": locator_status,
                             "server_recv_time": time_stamp
                             }
            if len(lnglat2) != 0:
                location_info["lnglat2"] = lnglat2
                location_info["radius2"] = radius2
            if len(lnglat3) != 0:
                location_info["lnglat3"] = lnglat3
                location_info["radius3"] = radius3
            logger.info("imei:%s pk:%s location:%s", pk, str_pk,
                        str(location_info))
            if pet_info is not None:
                yield self.pet_dao.add_location_info(pet_info["pet_id"],
                                                     pk.imei, location_info)
                # uid = pet_info.get("uid", None)
                # if uid is not None:
                #     msg = push_msg.new_location_change_msg(
                #         "%.7f" % lnglat[1], "%.7f" % lnglat[0],
                #         int(time.mktime(locator_time.timetuple())), radius)
                #     try:
                #         yield self.msg_rpc.push_android(uids=str(uid),
                #                                         payload=msg,
                #                                         pass_through=1)
                #         # ios去掉推送
                #         # yield self.msg_rpc.push_ios(uids=str(uid), payload=msg)
                #     except Exception, e:
                #         logger.exception(e)
        now_time = datetime.datetime.now()
        yield self.new_device_dao.update_device_info(
            pk.imei,
            status=pk.status,
            electric_quantity=pk.electric_quantity,
            j01_repoter_date=now_time,
            server_recv_time=time_stamp)

        battery_status = 0
        if pk.electric_quantity < LOW_BATTERY:
            battery_status = 1
            if pk.electric_quantity < ULTRA_LOW_BATTERY:
                battery_status = 2
        device_info = yield self.new_device_dao.get_device_info(pk.imei, ("battery_status",))
        # if device_info is not None:
        if not utils.battery_status_isequal(device_info.get("battery_status", 0), battery_status):
            yield self.new_device_dao.update_device_info(pk.imei, **{"battery_status": battery_status})
            yield self._SendBatteryMsg(pk.imei, pk.electric_quantity,
                                       battery_status, now_time)
        if pet_info is not None:
            sport_info = {}
            sport_info["diary"] = datetime.datetime.combine(
                datetime.date.today(), datetime.time.min)
            sport_info["step_count"] = pk.step_count
            sport_info["distance"] = pk.distance
            sport_info["calorie"] = pk.calorie
            sport_info["target_energy"] = pet_info.get("target_energy", 0)
            yield self.pet_dao.add_sport_info(pet_info["pet_id"], pk.imei,
                                              sport_info)

            if pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_MIXED:
                wifi_info = utils.change_wifi_info(pk.location_info.mac, True)
                common_wifi = pet_info.get("common_wifi", None)
                home_wifi = pet_info.get("home_wifi", None)
                new_common_wifi = utils.get_new_common_wifi(
                    common_wifi, wifi_info, home_wifi)
                uid = pet_info.get("uid", None)
                if uid is not None:
                    is_in_home = utils.is_in_home(home_wifi, new_common_wifi,
                                                  wifi_info)
                    self._SendPetInOrNotHomeMsg(pk.imei, is_in_home)
                yield self.pet_dao.add_common_wifi_info(pet_info["pet_id"],
                                                        new_common_wifi)

        if pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_MIXED:
            yield self.new_device_dao.report_wifi_info(pk.imei,
                                                       pk.location_info.mac)

        raise gen.Return(True)

    @gen.coroutine
    def _OnReportHealthInfoReq(self, conn_id, header, body, peer):
        # Parse packet
        pk = terminal_packets.ReportHealthInfoReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        logger.debug(
            "OnReportHealthInfoReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)
        self.updateDeviceStatus(pk.imei)
        # Ack
        sleep_data = []
        pet_info = yield self.pet_dao.get_pet_info(("pet_id",),
                                                   device_imei=pk.imei)
        if pet_info is None:
            logger.error("imei:%s pk:%s not found pet_info", pk, str_pk)
        else:
            try:
                for item in pk.sleep_data:
                    tmp = terminal_proto.FieldDict(item.fields)
                    sleep_data.append(tmp)
                ret = yield self.pet_dao.add_sleep_info(pet_info["pet_id"],
                                                        pk.imei, sleep_data)

            except Exception, e:
                logger.exception(e)
        ack = terminal_packets.ReportHealthInfoAck(header.sn)
        yield self._send_res(conn_id, ack, pk.imei, peer)
        raise gen.Return(True)

    @gen.coroutine
    def _OnSendCommandAck(self, conn_id, header, body, peer):
        # Parse packet
        pk = terminal_packets.SendCommandAck()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.debug(
            "OnSendCommandAck, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)

        self.unreply_msg_mgr.delete_unreply_msg(header.sn, pk.imei)

        raise gen.Return(True)

    @gen.coroutine
    def _OnHeartbeatReq(self, conn_id, header, body, peer):
        # Parse packet
        pk = terminal_packets.HeatbeatReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s parse_data=%s peer=%s' %
                      (header, body, str_pk, peer), pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)
        self.updateDeviceStatus(pk.imei)

        logger.info(
            "OnHeartbeatReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)

        # Ack
        ack = terminal_packets.HeatbeatAck(header.sn)
        yield self._send_res(conn_id, ack, pk.imei, peer)
        msgs = self.unreply_msg_mgr.get_un_reply_msg(pk.imei)
        logger.info("_OnHeartbeatReq  get imei:%s unreply_msgs:%s", pk.imei,
                    str(msgs))
        for msg in msgs:
            ret = yield self._broadcastor.send_msg_multicast((pk.imei,),
                                                             msg[1])
            ret_str = "send ok" if ret else "send fail"
            self._OnOpLog("s2c on connected retry  send_data:%s ret:%s" %
                          (msg, ret_str), pk.imei)
            logger.info("_OnHeartbeatReq s2c send_data:%s ret:%s imei:%s",
                        msg[1], ret_str, pk.imei)

        raise gen.Return(True)

    @gen.coroutine
    def _SendBatteryMsg(self, imei, battery, battery_statue, datetime):
        pet_info = yield self.pet_dao.get_pet_info(("pet_id", "uid", "device_os_int", "mobile_num"),
                                                   device_imei=imei)
        if pet_info is not None:
            uid = pet_info.get("uid", None)
            if uid is None:
                logger.warning("imei:%s uid not find", imei)
                return

            message = ''
            sms_type="low_battery"
            if battery_statue == 1:
                message = "设备低电量，请注意充电"
                sms_type = "low_battery"
                if (int)(pet_info.get('device_os_int', 23)) > 23 and pet_info.get('mobile_num') is not None:
                    self.msg_rpc.send_sms(sms_type,pet_info.get('mobile_num'), "低")
                    return
            elif battery_statue == 2:
                message = "设备超低电量，请注意充电"
                if (int)(pet_info.get('device_os_int', 23)) > 23 and pet_info.get('mobile_num') is not None:
                    sms_type = "superlow_battery"
                    self.msg_rpc.send_sms(sms_type,pet_info.get('mobile_num'), "超低")
                    return

            msg = push_msg.new_now_battery_msg(
                utils.date2str(datetime), battery, battery_statue)
            try:
                yield self.msg_rpc.push_android(uids=str(uid),
                                                payload=msg,
                                                pass_through=1)
                # ios去掉推送
                # yield self.msg_rpc.push_ios_useraccount(uids=str(uid),
                #                                         payload=msg)
                if battery_statue == 1:
                    yield self.msg_rpc.push_android(uids=str(uid),
                                                    title="小毛球智能提醒",
                                                    desc="追踪器电量低，请及时充电！",
                                                    payload=msg,
                                                    pass_through=0)
                    yield self.msg_rpc.push_ios_useraccount(uids=str(uid),
                                                            payload="追踪器电量低，请及时充电！",
                                                            extra="low_battery"
                                                            )
                elif battery_statue == 2:
                    yield self.msg_rpc.push_android(uids=str(uid),
                                                    title="小毛球智能提醒",
                                                    desc="追踪器电量超低，请及时充电！",
                                                    payload=msg,
                                                    pass_through=0)
                    yield self.msg_rpc.push_ios_useraccount(uids=str(uid),
                                                            payload="追踪器电量超低，请及时充电！",
                                                            extra="superlow_battery"
                                                            )


            except Exception, e:
                logger.exception(e)
        else:
            logger.warning("imei:%s uid not find", imei)

    @gen.coroutine
    def _OnReportTerminalStatusReq(self, conn_id, header, body, peer):
        # Parse packet
        pk = terminal_packets.ReportTerminalStatusReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.debug(
            "OnReportTerminalStatusReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)

        yield self.new_device_dao.update_device_info(
            pk.imei,
            iccid=unicode(pk.iccid),
            hardware_version=unicode(pk.hardware_version),
            software_version=unicode(pk.software_version),
            electric_quantity=pk.electric_quantity)

        now_time = datetime.datetime.now()
        battery_status = 0
        if pk.electric_quantity <= LOW_BATTERY:
            battery_status = 1
            if pk.electric_quantity <= ULTRA_LOW_BATTERY:
                battery_status = 2
        yield self._SendOnlineMsg(pk.imei, pk.electric_quantity, now_time)
        device_info = yield self.new_device_dao.get_device_info(pk.imei, ("battery_status",))
        if device_info is not None:
            if not utils.battery_status_isequal(device_info.get("battery_status", 0), battery_status):
                yield self.new_device_dao.update_device_info(pk.imei, **{"battery_status": battery_status})
                yield self._SendBatteryMsg(pk.imei, pk.electric_quantity,
                                           battery_status, now_time)

        # Ack
        ack = terminal_packets.ReportTerminalStatusAck(header.sn, 0)
        yield self._send_res(conn_id, ack, pk.imei, peer)

        raise gen.Return(True)

    @gen.coroutine
    def _OnSyncCommandReq(self, conn_id, header, body, peer):
        pk = terminal_packets.SyncCommandReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.debug(
            "OnSyncCommandReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)

        # Ack
        # command_pk = terminal_commands.SOS(("18666023586", "18666023585"))
        command_pk = TEST_S2C_COMMAND_DATA.get(pk.command, None)
        if command_pk is None:
            logger.error("OnSyncCommandReq command:%s not find", pk.command)
        else:
            ack = terminal_packets.SyncCommandResp(header.sn, command_pk, 0)
            yield self._send_res(conn_id, ack, pk.imei, peer)

        raise gen.Return(True)

    @gen.coroutine
    def _OnUploadTerminalLogReq(self, conn_id, header, body, peer):
        # Parse packet
        pk = terminal_packets.UploadTerminalLogReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.debug(
            "OnUploadTerminalLogReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)

        log_items = []
        try:
            log_items = [terminal_proto.FieldDict(item.fields)
                         for item in pk.log_items]
        except Exception, e:
            pass
        yield self.new_device_dao.add_terminal_log(pk.imei, log_items)
        # Ack
        ack = terminal_packets.UploadTerminalLogAck(header.sn, 0)
        yield self._send_res(conn_id, ack, pk.imei, peer)

        raise gen.Return(True)

    @gen.coroutine
    def _OnUploadStationLocationReq(self, conn_id, header, body, peer):
        pk = terminal_packets.UploadStationReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.debug(
            "_OnUploadStationLocationReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)
        ret = yield self.get_location_by_bts_info(
            pk.imei, pk.station_locator_data, None)
        lng = float(0)
        lat = float(0)
        if ret is not None:
            lng, lat = ret

        ack = terminal_packets.UploadStationAck(header.sn, lng, lat)
        yield self._send_res(conn_id, ack, pk.imei, peer)
        raise gen.Return(True)

    @gen.coroutine
    def _OnGpsSwitchReq(self, conn_id, header, body, peer):
        pk = terminal_packets.GPSSwtichReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.debug(
            "_OnGpsSwitchReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)

        ack = terminal_packets.GPSSwtichAck(header.sn, 1)
        yield self._send_res(conn_id, ack, pk.imei, peer)

        raise gen.Return(True)

    @gen.coroutine
    def _OnGetLocationReq(self, conn_id, header, body, peer):
        pk = terminal_packets.ReportLocationInfoReq()
        pk.Parse(body)
        str_pk = str(pk)

        logger.debug(
            "_OnGetLocationReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        locator_time = pk.location_info.locator_time
        lnglat = []
        if pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_GPS:

            lnglat = [float(pk.location_info.longitude),
                      float(pk.location_info.latitude)]
        elif pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_STATION:
            ret = yield self.get_location_by_bts_info(
                pk.imei, pk.location_info.station_locator_data, None)
            if ret is not None:
                lnglat = ret
        elif pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_MIXED:

            ret = yield self.get_location_by_mixed(
                pk.imei, pk.location_info.station_locator_data, None,
                pk.location_info.mac)
            if ret is not None:
                lnglat = ret
        else:
            logger.warning("imei:%s location fail", pk.imei)
        self._OnOpLog('c2s header=%s pk=%s peer=%s' % (header, str_pk, peer),
                      pk.imei)
        time_stamp = int(time.time())
        if len(lnglat) != 0:
            location_info = {"lnglat": lnglat,
                             "locator_time": pk.location_info.locator_time,
                             "server_recv_time": time_stamp
                             }
            logger.info("imei:%s pk:%s location  lnglat:%s", pk, str_pk,
                        str(lnglat), time_stamp)
            yield self.new_device_dao.add_location_info(pk.imei, location_info)

        yield self.new_device_dao.update_device_info(
            pk.imei,
            status=pk.status,
            electric_quantity=pk.electric_quantity,
            server_recv_time=time_stamp
        )

        pet_info = yield self.pet_dao.get_pet_info(
            ("pet_id", "uid", "home_wifi", "common_wifi", "target_energy"),
            device_imei=pk.imei)
        if pet_info is not None:
            sport_info = {}
            sport_info["diary"] = datetime.datetime.combine(
                datetime.date.today(), datetime.time.min)
            sport_info["step_count"] = pk.step_count
            sport_info["distance"] = pk.distance
            sport_info["calorie"] = pk.calorie
            sport_info["target_energy"] = pet_info.get("target_energy", 0)
            yield self.new_device_dao.add_sport_info(pk.imei, sport_info)
        raise gen.Return(True)

    @gen.coroutine
    def _SendPetInOrNotHomeMsg(self, imei, is_in_home):
        pet_info = yield self.pet_dao.get_pet_info(
            ("pet_id", "uid","nick", "pet_is_in_home", "device_os_int", "mobile_num"),
            device_imei=imei)
        if pet_info is not None:
            uid = pet_info.get("uid", None)
            if uid is None:
                logger.warning("imei:%s uid not find", imei)
                return
            pet_is_in_home = pet_info.get("pet_is_in_home", 1)
            if (pet_is_in_home == 1 and is_in_home) or (
                            pet_is_in_home == 0 and not is_in_home):
                return
            yield self.pet_dao.update_pet_info(
                pet_info["pet_id"], pet_is_in_home=1 - pet_is_in_home)

            msg = push_msg.new_pet_not_home_msg()
            if is_in_home:
                msg = push_msg.new_pet_in_home_msg()
            try:
                yield self.msg_rpc.push_android(uids=str(uid),
                                                payload=msg,
                                                pass_through=1)
                # yield self.msg_rpc.push_ios_useraccount(uids=str(uid),
                #                                         payload=msg)
            except Exception, e:
                logger.exception(e)

            message = ""
            sms_type="at_home"
            nick=pet_info.get("nick","宠物")
            if is_in_home:
                message = nick+"已安全到家。"
                sms_type="at_home"
            else:
                message = nick+"可能离家，请确认安全。"
                sms_type = "out_home"

            if (int)(pet_info.get('device_os_int', 23)) > 23 and pet_info.get('mobile_num') is not None:
                self.msg_rpc.send_sms(sms_type,pet_info.get('mobile_num'), nick)
                return

            try:
                if (is_in_home):
                    yield self.msg_rpc.push_android(uids=str(uid),
                                                    title="小毛球智能提醒",
                                                    desc=message,
                                                    payload=msg,
                                                    pass_through=0)
                    yield self.msg_rpc.push_ios_useraccount(uids=str(uid),
                                                            payload=message,
                                                            extra="in_home"
                                                            )
                else:
                    yield self.msg_rpc.push_android(uids=str(uid),
                                                    title="小毛球智能提醒",
                                                    desc=message,
                                                    payload=msg,
                                                    pass_through=0)
                    yield self.msg_rpc.push_ios_useraccount(uids=str(uid),
                                                            payload=message,
                                                            extra="out_home"
                                                            )




            except Exception, e:
                logger.exception(e)
        else:
            logger.warning("imei:%s uid not find", imei)

    @gen.coroutine
    def _SendOnlineMsg(self, imei, battery, datetime):
        pet_info = yield self.pet_dao.get_pet_info(("pet_id", "uid"),
                                                   device_imei=imei)
        if pet_info is not None:
            uid = pet_info.get("uid", None)
            if uid is None:
                logger.warning("imei:%s uid not find", imei)
                return
            msg = push_msg.new_device_on_line_msg(battery,
                                                  utils.date2str(datetime))
            self.updateDeviceStatus(imei)

            try:
                yield self.msg_rpc.push_android(uids=str(uid),
                                                payload=msg,
                                                pass_through=1)
                # yield self.msg_rpc.push_ios_useraccount(uids=str(uid), payload=msg,
                #                             extra={"type":"online"}
                #                             )
            except Exception, e:
                logger.exception(e)

        else:
            logger.warning("imei:%s uid not find", imei)

            # 更新在线状态

    @gen.coroutine
    def updateDeviceStatus(self, imei):
        pet_info = yield self.pet_dao.get_pet_info(("pet_id", "uid"),
                                                   device_imei=imei)
        if pet_info is not None:
            yield self.pet_dao.update_pet_info(pet_info["pet_id"],
                                               device_status=1
                                               )

    @gen.coroutine
    def _OnImeiExpires(self, imeis):
        logger.debug("_OnImeiExpires imeis:%s", str(imeis))

        for imei in imeis:
            conn_id=self._broadcastor.get_connid_by_imei(imei)
            if conn_id is not None:
                conn = self.conn_mgr.GetConn(conn_id)
                if conn is not None:
                    conn.close()
            pet_info = yield self.pet_dao.get_pet_info(("pet_id", "uid"),
                                                       device_imei=imei)
            if pet_info is not None:
                uid = pet_info.get("uid", None)
                if uid is None:
                    logger.warning("imei:%s uid not find", imei)
                    continue
                msg = push_msg.new_device_off_line_msg()
                self.pet_dao.update_pet_info(pet_info["pet_id"],
                                             device_status=0
                                             )
                try:
                    yield self.msg_rpc.push_android(uids=str(uid),
                                                    payload=msg,
                                                    pass_through=1)
                    # yield self.msg_rpc.push_ios(uids=str(uid), payload=msg)
                    # yield self.msg_rpc.push_ios_useraccount(uids=str(uid), payload=msg,
                    #                                         extra={"type": "offline"})
                    logger.debug("_OnImeiExpires imeis success:%s", str(imeis))
                except Exception, e:
                    logger.exception(e)

            else:
                logger.warning("imei:%s uid not find", imei)

    @gen.coroutine
    def _OnUnreplyMsgsSend(self, reply_msgs):
        logger.debug("_OnUnreplyMsgsSend reply_msgs:%s", str(reply_msgs))
        for sn, imei, msg, count in reply_msgs:
            ret = yield self._broadcastor.send_msg_multicast((imei,), msg)
            ret_str = "send ok" if ret else "send fail"
            self._OnOpLog("s2c retry count:%d send_data:%s ret:%s" %
                          (count, msg, ret_str), imei)
            logger.info(
                "_OnUnreplyMsgsSend s2c retry count:%d send_data:%s ret:%s imei:%s",
                count, msg, ret_str, imei)

    @run_on_executor
    def get_location_by_bts_info(self, imei, bts_info, near_bts_infos):
        return get_location_by_bts_info(imei, bts_info, near_bts_infos)

    @run_on_executor
    def get_location_by_wifi(self, imei, macs):
        return get_location_by_wifi(imei, macs)

    @run_on_executor
    def get_location_by_mixed(self, imei, bts_info, near_bts_infos, macs):
        return get_location_by_mixed(imei, bts_info, near_bts_infos, macs)
