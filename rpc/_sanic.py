from sanic import Sanic, text

from ._vendor.log import logging

Sanic.START_METHOD_SET = True
Sanic.start_method = "fork"

app = Sanic("qw")


from .utils import collectInfo

_RPCParser_ = None


@app.post("/")
def runRpcFunction(req):
    return text(_RPCParser_.serializationResponse(_RPCParser_(_RPCParser_.obj, req.body.decode())))


@app.get("/")
def getInfo(req):
    return text(collectInfo(_RPCParser_))


def startServer(*args, route=r"/", port=8152, process=0, **kargs):
    if process == 0:
        import multiprocessing

        process = multiprocessing.cpu_count()
    app.run(host="0.0.0.0", port=int(port), workers=int(process))
