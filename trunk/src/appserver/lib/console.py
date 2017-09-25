# -*- coding: utf-8 -*-

import logging

import tornado.tcpserver
import tornado.ioloop

from tornado import gen

class Console(tornado.tcpserver.TCPServer):
    def __init__(self):
        tornado.tcpserver.TCPServer.__init__(self)
    
    @gen.coroutine
    def _read_line(self, stream, address):
        yield stream.write(">>")
        
        line = yield stream.read_until("\n", None, 1024)
        line = line.strip()
        self.handle_line(stream, address, line)
    
    def handle_stream(self, stream, address):
        logging.debug("A new console client, peer=%s", str(address))
        self._read_line(stream, address)
    
    def handle_line(self, stream, address, line):
        logging.debug("Receive a console line \"%s\", peer=%s", line, address)
        
        cmd = []
        if line:
            cmd = line.split(' ')
        if not self.handle_cmd(stream, address, cmd):
            stream.close()
        
        self._read_line(stream, address)
    
    def handle_cmd(self, stream, address, cmd):
        return False
    
    @gen.coroutine
    def send_response(self, stream, response):
        yield stream.write(response + "\r\n")
        
if __name__ == "__main__":
    class _MyConsole(Console):
        def handle_cmd(self, stream, address, cmd):
            if len(cmd) == 1 and cmd[0] == "quit":
                self.send_response(stream, "Byte!")
                return False
            elif len(cmd) == 0:
                return True
            else:
                self.send_response(stream, "Invalid command!")
                return True

    import tornado.options

    tornado.options.parse_command_line()

    c = _MyConsole()
    c.bind(9090, "127.0.0.1")
    c.start()
    tornado.ioloop.IOLoop.current().start()

