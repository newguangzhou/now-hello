# -*- coding: utf-8 -*-

import logging
import traceback
import os
import importlib
import sys


class PyLoader:
    def __init__(self, module):
        self._module = module
        self._mod_inst = None

    def ReloadInst(self, class_name, *args, **kwargs):
        inst = None

        # First we try to reload module
        tmpmod = None
        if sys.modules.has_key(self._module):
            del sys.modules[self._module]
        try:
            tmpmod = importlib.import_module(self._module)
        except Exception, e:
            logging.error(
                "Can not reload inst, import error, module=\"%s\" class_name=\"%s\" trace=\"%s\"",
                self._module, class_name, traceback.format_exc())

            if self._mod_inst:
                sys.modules[self._module] = self._mod_inst
                inst = getattr(self._mod_inst, class_name)(*args, **kwargs)
            return inst

        # Try to create a instance
        try:
            inst = getattr(tmpmod, class_name)(*args, **kwargs)
        except Exception, e:
            logging.error(
                "Reload inst error, module=\"%s\" class_name=\"%s\" trace=\"%s\"",
                self._module, class_name, traceback.format_exc())

            if sys.modules.has_key(self._module):
                del sys.modules[self._module]

            if self._mod_inst:
                sys.modules[self._module] = self._mod_inst
                inst = getattr(self._mod_inst, class_name)(*args, **kwargs)

        self._mod_inst = tmpmod
        return inst


if __name__ == "__main__":
    import tornado.ioloop
    import tornado.options

    from tornado.options import define, options

    import console

    class _TestConsole(console.Console):
        def handle_cmd(self, stream, address, cmd):
            if len(cmd) == 1 and cmd[0] == "quit":
                self.send_response(stream, "Byte!")
                return False
            elif len(cmd) == 0:
                pass
            elif len(cmd) == 1 and cmd[0] == "reload-config":
                conf = self.pyld.ReloadInst("TestConfig")
                logging.debug("Reload after:%s", str(conf))
                self.send_response(stream, "done")
            else:
                self.send_response(stream, "Invalid command!")
            return True

    tornado.options.parse_command_line()

    pyld = PyLoader("test_config")

    conf = pyld.ReloadInst("TestConfig")
    logging.debug("Reload before:%s", str(conf))

    c = _TestConsole()
    c.pyld = pyld
    c.bind(9090, "127.0.0.1")
    c.start()
    tornado.ioloop.IOLoop.current().start()
