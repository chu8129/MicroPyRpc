import tornado
from tornado.web import RequestHandler

from ._vendor.log import logging


class TornadoRPCHandler(RequestHandler):
    _RPCParser_ = None
    obj = None

    @tornado.gen.coroutine
    def post(self):
        yield self.writeToSocketResponse(self._RPCParser_.serializationResponse(self._RPCParser_(self.obj, self.request.body)))

        # res = yield self._post()
        # return self.writeToSocketResponse(res)  # reason:use main process io_loop

    # import concurrent
    # executor = concurrent.futures.ThreadPoolExecutor(2)

    # @tornado.concurrent.run_on_executor
    # def _post(self):
    #     pass

    def writeToSocketResponse(self, response_text):
        self.set_header("Content-Type", self._RPCParser_.content_type)
        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.write(response_text)

    @tornado.gen.coroutine
    def get(self):
        self.clear_all_cookies()
        from .utils import collectInfo

        self.write(collectInfo(self))


def startServer(handlers, route=r"/", port=8152, process=0):
    from sys import platform

    process = process if platform != "darwin" else 1
    logging.info("tornado fork process num:%s, platform:%s" % (process, platform))

    from tornado.platform.asyncio import AsyncIOMainLoop

    AsyncIOMainLoop().install()

    if not isinstance(handlers, (list, tuple, set)):
        handler = handlers
        handlers = [(route, handler)]

    import tornado.web

    application = tornado.web.Application(handlers, debug=False, autoreload=False, compress_response=True)

    from tornado.httpserver import HTTPServer as _Server

    global server
    server = _Server(application)

    # import tornado.netutil

    # server.add_socket(tornado.netutil.bind_unix_socket("/dev/shm/tornado.socket"))

    (server.listen(port) if platform != "darwin" else server.bind(port))
    server.start(process)

    handler.obj.runAfterServerStart()

    import tornado.ioloop

    try:
        print("start instance")
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        logging.error(e, exc_info=True)
        tornado.ioloop.IOLoop.instance().stop()
