"""End-to-end test: a stdlib HTTP server wraps the RPC parser and the built-in
ClientConnect calls it over real HTTP. No optional backend required.

Run with: python tests/test_rpc.py
"""

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rpc.base import BaseRPCParser, ClientConnect, Fault
from rpc.json import updateClient, updateParser

updateParser(BaseRPCParser)
updateClient(ClientConnect)


class Obj:
    class Inner:
        def ping(self):
            return "pong"

    def __init__(self):
        self.inner = Obj.Inner()

    def add(self, a, b):
        return a + b

    def echo(self, value):
        return value

    def boom(self):
        raise ValueError("kaboom")


obj = Obj()
parser = BaseRPCParser()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        out = parser.serializationResponse(parser(obj, body))
        data = out.encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json-rpc")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def _serve():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, "http://127.0.0.1:%d" % server.server_address[1]


def test_parser_and_client():
    server, url = _serve()
    try:
        client = ClientConnect(url)
        assert client.obj.add(1, 2) == 3
        assert client.obj.add(a=10, b=5) == 15
        assert client.obj.inner.ping() == "pong"
        assert client.obj.echo("hello") == "hello"

        try:
            client.obj.boom()
            raise AssertionError("expected server exception to propagate")
        except AssertionError:
            raise
        except Exception as e:
            assert "kaboom" in str(e)

        try:
            client.obj.nope()
            raise AssertionError("expected method-not-found to raise")
        except AssertionError:
            raise
        except Exception:
            pass

        raw = parser.serializationResponse(parser(obj, json.dumps({"method": "nope", "params": [], "id": "9"})))
        assert json.loads(raw)["status"] is False
    finally:
        server.shutdown()


def test_fault():
    fault = Fault()
    assert fault.error() == {"code": -32000, "message": "Server error"}


if __name__ == "__main__":
    test_parser_and_client()
    test_fault()
    print("ALL PASS")
