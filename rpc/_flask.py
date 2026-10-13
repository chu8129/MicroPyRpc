from flask import Flask, request

from ._vendor.log import logging

app = Flask(__name__)


from .utils import collectInfo

_RPCParser_ = None


@app.route("/", methods=["POST"])
def runRpcFunction():
    return _RPCParser_.serializationResponse(_RPCParser_(_RPCParser_.obj, request.get_data()))


@app.route("/", methods=["GET"])
def getInfo():
    return collectInfo(_RPCParser_)


def startServer(*args, route=r"/", port=8152, process=0, **kargs):
    import sys

    if process == 0:
        import multiprocessing

        process = multiprocessing.cpu_count()

    # werkzeug only supports multi-process servers via fork (POSIX). On other
    # platforms (e.g. Windows) fall back to a single threaded process.
    threaded = False
    if not sys.platform.startswith("linux"):
        process = 1
        threaded = True

    logging.info("process:%s threaded:%s" % (process, threaded))
    app.run(host="0.0.0.0", port=port, debug=True, threaded=threaded, processes=process, use_reloader=False)
