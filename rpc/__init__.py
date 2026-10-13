#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = "qwwang(mail:chu8129@gmail.com) @ 2024-03-27 18:07:11"

# 获取函数信息文档, curl http://localhost:port

from .base import BaseRPCParser
from .json import updateParser

updateParser(BaseRPCParser)


# main
def useTornado(ServerInfer, *args, **kargs):
    from ._tnd import TornadoRPCHandler

    class Handler(TornadoRPCHandler):
        _RPCParser_ = BaseRPCParser()
        obj = ServerInfer(False)

    from ._tnd import startServer as _start_server

    process = kargs.get("process", 0)
    # process = Handler.obj.processNum if Handler.obj.processNum > 0 else process
    _start_server(Handler, port=kargs["port"], process=process)


def useFlask(ServerInfer, *args, **kargs):
    class Handler(BaseRPCParser):
        obj = ServerInfer()

    from . import _flask

    _flask._RPCParser_ = Handler()
    _flask.startServer(port=kargs["port"])


def useZeroGevent(ServerInfer, *args, **kargs):
    import os

    if int(os.environ.get("useGevent", 0)):
        from gevent import monkey

        monkey.patch_all()

    import zerorpc

    def v0():
        obj = ServerInfer()
        obj.lock = None
        s = zerorpc.Server(obj, heartbeat=None, pool_size=10)
        s.bind(f"tcp://0.0.0.0:{kargs['port']}")
        # s.run()
        zerorpc.gevent.spawn(s.run)

    v0()
    while 1:
        zerorpc.gevent.sleep(1)


def sanic(ServerInfer, *args, **kargs):
    class Handler(BaseRPCParser):
        obj = ServerInfer()

    from . import _sanic

    _sanic._RPCParser_ = Handler()
    _sanic._start_server(port=kargs["port"])


def useTcp(ServerInfer, *args, **kargs):
    from ._zmq import Server

    class Handler(Server):
        _RPCParser_ = BaseRPCParser()
        obj = ServerInfer()

    Handler(kargs["port"])()


def server(ServerInfer, *args, **kargs):
    agreement = kargs["agreement"]

    # flask 和 onnxruntime 相冲突有bug
    return dict(
        zero2=useTornado,
        flask=useFlask,
        gevent=useZeroGevent,
        sanic=sanic,
        tcp=useTcp,
    ).get(
        agreement.strip().lower(), useZeroGevent
    )(ServerInfer, *args, **kargs)


if __name__ == "__main__":
    import fire

    fire.Fire()
