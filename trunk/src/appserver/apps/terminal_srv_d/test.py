# -*- coding: utf-8 -*-

import socket
from terminal_base import terminal_proto
sock = socket.socket()

#sock.connect(("120.24.152.121", 5050))
sock.connect(("127.0.0.1", 5050))
proto_io = terminal_proto.ProtoIO()


def SendMsg(msg):
    return sock.send(msg)


def RecvMsg():
    rt = sock.recv(1024)
    if not rt:
        print "Conn is closed by peer"
        return None

    proto_io.read_buff.AppendData(rt)

    # Read packets
    while True:
        header, body = proto_io.Read()
        if not header:
            break

        print "Receive a message, header=\"%s\" body=\"%s\"" % (str(header),
                                                                body)

    # Rewind buffer
    proto_io.read_buff.Rewind()

# Test report location info
#location_info1 = "0E121.411783N31.178125T20080121165030"
#location_info2 = "2460,01,40977,22054 09,-65|460,01,40977, 2205409,-65|460,01, 40977,2205409,-65T20080121165030"
#location_ainfo = "00,100,2222,3333,4444"
#msg_header = "200710231200001000,J01,%d,123456789012345"

#tmp = "@" + location_info1 + "#" + location_ainfo
#msg1 = "[" + msg_header % (15 + len(tmp), ) + tmp + "]"

#n = SendMsg(msg1)
#print "Send:%d" % (n, )
#RecvMsg()

#tmp = "@" + location_info2 + "#" + location_ainfo
#msg2 = "[" + msg_header % (15 + len(tmp), ) + tmp + "]"
#n = SendMsg(msg2)
#print "Send:%d" % (n, )
#RecvMsg()

# Test report health info
#msg = "[200710231200001000,J02,61,123456789012345@1201604181650300656,10000#2,20160418165030,75]"
#SendMsg(msg)
#RecvMsg()

# Test send command ack
#msg = "[200710231200001000,R03,19,123456789012345@009]"
#SendMsg(msg)

# Test heartbeat
#msg = "[][201706111802020250,J"
#SendMsg(msg)
#RecvMsg()

msg = "[201707092056000253,J12,21,357396080001200@Heart]"
SendMsg(msg)
RecvMsg()
RecvMsg()

RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()
RecvMsg()

# Test report terminal status
#msg = "[200710231200001000,J17,43,123456789012345@13501530329%1.0.0%1.0.0%100]"
#SendMsg(msg)
#RecvMsg()

# Test upload terminal log
#msg = "[200710231200001000,J18,66,123456789012345@20160418165030,1%20160418165031,2%20160418165032,3]"
#SendMsg(msg)
#RecvMsg()

#msg = "[201612091206040539,J01,104,358688000000152@2460,0,9365,4190,28|460,0,9365,3701,12|460,0,9365,4213,4|T20161209120604#00,200,0,5522,0]"
#SendMsg(msg)
#RecvMsg()

#msg = "[201612101754030001,J02,63,358688000000152@1,20161210175403,2880,1#1,20161214175403,2800,2]"
#SendMsg(msg)

#msg = "[201612101718370000,J01,159,358688000000152@5460,0,9365,4190,28|460,0,9365,3701,12|460,0,9365,4213,4%F0:B4:29:51:11:19,-50,TP-LINK|F0:B4:29:51:11:19,-50,TP-LINK|T20161210171837#00,0,0,0,0]"
#SendMsg(msg)
#RecvMsg()
#msg = "[201612131327230079,J01,70,358688000000152@0E113.997118N22.593125T20161213132722#00,89,0,3235,456]"
#SendMsg(msg)
#RecvMsg()
#msg = "[201612071757470000,J17,66,358688000000152@89886970205072101022%X2_Plus_V1.1%X2_Plus_V1.0%100]"
#SendMsg(msg)
#RecvMsg()

#msg = "[201612101754030001,J02,64,123456789012345@1,20161210175403,28800,1#1,20161214175403,2800,2]"
#SendMsg(msg)

#msg = "[]"
#SendMsg(msg)
#RecvMsg()

#msg = "[200710231200001000,J18,66,123456789012345@20160418165030,1%20160418165031,2%20160418165032,3]"
#SendMsg(msg)
#RecvMsg()
