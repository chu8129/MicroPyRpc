# TODO wang.qiuwen wait fix
import json
import threading

import zmq

from ._vendor.decorator import timeFunc


class Server:
    _RPCParser_ = None

    def __init__(self, port=None, threads=1):
        self.port = port
        self.threads = threads

    def _server(self, context):
        with context.socket(zmq.DEALER) as worker:
            worker.connect("inproc://backend")
            while True:
                ident, msg = worker.recv_multipart()
                try:
                    msg = self._RPCParser_.serializationResponse(self._RPCParser_(self, msg))
                except Exception as e:
                    msg = json.dumps({"code": 1, "error": str(e)})
                worker.send_multipart([ident, msg.encode()])

    def __call__(self):
        with zmq.Context() as context:
            with context.socket(zmq.ROUTER) as frontend, context.socket(zmq.DEALER) as backend:
                frontend.bind(f"tcp://*:{self.port}")
                backend.bind("inproc://backend")

                workers = []

                for i in range(self.threads):
                    worker = threading.Thread(target=self._server, args=(context,))
                    worker.start()
                    workers.append(worker)

                try:
                    zmq.proxy(frontend, backend)

                except Exception as e:
                    import traceback

                    traceback.print_exc()

                    for thread in workers:
                        thread.join()


def testServer():
    Server(port=8152)()


from .base import ClientConnect


class Client(ClientConnect):
    library = None

    @timeFunc
    def _onRequest(self, url, data, *args, **kargs):
        with zmq.Context() as context:
            with context.socket(zmq.DEALER) as socket:
                socket.setsockopt(zmq.HEARTBEAT_IVL, 1)
                socket.setsockopt(zmq.HEARTBEAT_TTL, 10)
                socket.setsockopt(zmq.HEARTBEAT_TIMEOUT, 1)
                socket.connect(f"tcp://127.0.0.1:{self.uri}")
                poll = zmq.Poller()
                poll.register(socket, zmq.DEALER)
                socket.send_string(data)
                while 1:
                    sockets = dict(poll.poll(100))
                    print(sockets)

                    # if not(sockets):
                    #     raise RuntimeError()

                    # if socket in sockets and sockets[socket] == zmq.POLLIN:

                    if socket in sockets:
                        res = socket.recv()
                        return res.decode()


def testClient():
    from .json import updateClient

    updateClient(Client)

    # return Client(8152).obj.requests({"url": "http://www.baidu.com", "method": "get"})
    # return Client(8152).obj.eval("1+1")
    return Client(8152).obj.eval("time.sleep(1)")


if __name__ == "__main__":
    import fire

    fire.Fire()
