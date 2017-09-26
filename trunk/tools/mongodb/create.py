# -*- coding: utf-8 -*-

import sys
import getopt
import os
import json

reload(sys)
sys.setdefaultencoding('utf-8')

import pymongo

def _usage():
    print "Usage:  --ip               要绑定的ip，默认为127.0.0.1"
    print "        --port             端口, 默认值为27018"
    print "        --name             该实例所在的replica set的名称, 必须指定"
    print "        --mem              要创建的数据库要使用的内存的最大大小以GB为单位, 默认为1GB"
    print "        --other-repl-hosts 该实例所在的其他replica set主机列表, 格式为 host:port,host:port,..."
    print "        --log-dir          日志目录，默认为/data/mongodb/logs/$name_$port"
    print "        --db-dir           数据库文件存放目录, 默认为/data/mongodb/data/$name_$port"
    print "        --mongod-path      用来指定mongod执行文件路径, 默认为mongod"
    print "        --mongo-path       用来指定mongo的执行文件路径, 默认为mongo"
    print "        --key-file         replica set认证所必须的key，默认为mongo.key"
    print "        --no-bind          不要在指定的ip上进行监听绑定"
    sys.exit(1)

_MONGO_DEFAULT_ARGS = "--fork --nohttpinterface --logappend --profile 1 \
    --storageEngine wiredTiger \
    --wiredTigerDirectoryForIndexes --directoryperdb"

def _exc_shell_cmd(cmd):
    return os.system(cmd)

def _shutdown_inst(mongod_path, db_dir):
    cmd = "%s --dbpath %s --shutdown" % (mongod_path, db_dir)
    if _exc_shell_cmd(cmd):
        print "Shutdown mongodb inst failed, dbpath=\"%s\"" % (db_dir,)
        return
    
opt_defines = ["ip=", "port=", "name=", "key-file=",
               "log-dir=", "db-dir=",
                "mem=", "other-repl-hosts=",
               "mongod-path=", "mongo-path=",
               "no-bind"]

if __name__ == "__main__":
    opts = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", opt_defines)
    except getopt.GetoptError, err:
        print str(err)
        _usage()
    
    if not opts:
        _usage()
    
    ip = None
    port = 27018
    name = None 
    log_dir = None
    other_repl_hosts = None
    mem = 1
    db_dir = None
    mongod_path = "/usr/bin/mongod"
    mongo_path = "mongo"
    key_file = "./mongo.key"
    no_bind = False
    
    try:
        for (o, a) in opts:
            if o == "--port":
                port = int(a)
            elif o == "--ip":
                ip = a
            elif o == "--name":
                name = a
            elif o == "--key-file":
                key_file = a
            elif o == "--log-dir":
                log_dir = a
            elif o == "--no-bind":
                no_bind = True
            elif o == "--other-repl-hosts":
                other_repl_hosts = a.split(",")
                for v in other_repl_hosts:
                    if len(v.split(":")) != 2:
                        raise
            elif o == "--mem":
                mem = int(a)
                if mem <= 0:
                    raise
            elif o == "--db-dir":
                db_dir = a
            elif o == "--mongod-path":
                mongod_path = a
            elif o == "--mongo-path":
                mongo_path = a
            else:
                print "未知的命令行选项\"%s\"" % (o,)
                _usage()
    except Exception,e:
        print "命令行参数错误"
        _usage()
    
    if not name:
        print "必须指定名称"
        _usage()
    
    if not log_dir:
        log_dir = "/data/mongodb/logs/%s_%u/" % (name,port)
    
    if not db_dir:
        db_dir = "/data/mongodb/data/%s_%u/" % (name,port)
    
    # 检查日志和数据库目录是否存在否则则创建
    if _exc_shell_cmd("if [ ! -d \"%s\" ]; then mkdir -p %s; fi" % (log_dir, log_dir)):
        print "Create log directory \"%s\" failed" % (log_dir,)
        sys.exit(1)
    if _exc_shell_cmd("if [ ! -d \"%s\" ]; then mkdir -p %s; fi" % (db_dir, db_dir)):
        print "Create db directory \"%s\" failed" % (db_dir,)
        sys.exit(1) 
    
    # 生成要用于启动mongodb的参数
    mongo_args = _MONGO_DEFAULT_ARGS
    if ip and not no_bind:
        mongo_args += " --bind_ip %s,127.0.0.1" % (ip,)
    mongo_args += " --port %u" % (port,)
    mongo_args += " --logpath %s" % (log_dir + "mongod.log",)
    mongo_args += " --replSet %s" % (name,)
    mongo_args += " --dbpath %s" % (db_dir,)
    mongo_args += " --wiredTigerCacheSizeGB %u" % (mem,)
    mongo_args += " --keyFile %s" % (key_file,)
    
    # 启动mongodb
    mongod_cmd = "%s %s" % (mongod_path, mongo_args)
    print "Start mongodb server, cmd=\"%s\"" % (mongod_cmd,)
    if _exc_shell_cmd(mongod_cmd):
        print "Start mongodb server failed!"
        sys.exit(1)
    print "Start mongodb server successed"
    
    # 设置其他repl set
    try:
        if other_repl_hosts:
            config = "{_id:\'%s\', members:[" % (name,)
            config += "{_id:0, host:\'%s:%u\'}," % (ip, port)
            i = 1
            for v in other_repl_hosts:
                config += "{_id:%u, host:\'%s\'}" % (i, v)
                if i != len(other_repl_hosts):
                    config += ","
                i += 1 
            config += "]}"
            cmd_base = "%s --host %s --port=%u --eval " % (mongo_path, ip, port)
            
            cmd = cmd_base + "\"rs.initiate(%s)\"" % (config,)
            
            print cmd
            if _exc_shell_cmd(cmd):
                print "Set repl other hosts failed"
                raise
            print "Set repl other hosts successed"
    except Exception,e:
        print "Set repl other hosts, error=\"%s\"" % (str(e),)
        _shutdown_inst(mongod_path, db_dir)
        sys.exit(1)

    sys.exit(0)
    
