from flask import Flask, request

from ._vendor.log import logging

app = Flask(__name__)


from .utils import collectInfo

_RPCParser_ = None


@app.route("/", methods=["POST"])
def runRpcFunction():
    return _RPCParser_.serializationResponse(_RPCParser_(_RPCParser_, request.get_data()))


@app.route("/", methods=["GET"])
def getInfo():
    return collectInfo(_RPCParser_)


def startServer(*args, route=r"/", port=8152, process=0, **kargs):
    if process == 0:
        import multiprocessing

        process = multiprocessing.cpu_count()
    logging.info("process:%s" % process)
    app.run(host="0.0.0.0", port=port, debug=True, threaded=False, processes=process, use_reloader=False)
