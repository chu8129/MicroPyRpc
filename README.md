# rpc-service

Standalone JSON-RPC service

## Layout

```
rpc/
  __init__.py      # server() dispatch + useTornado/useFlask/useZeroGevent/sanic/useTcp
  base.py          # BaseRPCParser, Fault, ClientConnect
  json.py          # JSON codec wiring (updateParser / updateClient)
  utils.py         # collectInfo -> GET / function docs
  _flask.py        # flask backend
  _sanic.py        # sanic backend
  _tnd.py          # tornado backend
  _zmq.py          # zeroMQ tcp backend + client
  _vendor/         # vendored helpers (config, log, decorator, common)
```

## Install

```bash
pip install -e .
# optional backends
pip install -e ".[flask,tornado]"
```

## Usage

Implement a server object whose public methods are exposed over RPC, then
start one of the provided servers:

```python
import rpc


class MyServer:
    def add(self, a, b):
        return a + b


if __name__ == "__main__":
    rpc.server(MyServer, agreement="flask", port=8152)
```

Supported `agreement` values: `flask`, `sanic`, `zero2` (tornado),
`gevent` (zerorpc), `tcp` (zeroMQ).

Call it with the built-in client:

```python
from rpc.base import ClientConnect
from rpc.json import updateClient

updateClient(ClientConnect)
client = ClientConnect("http://127.0.0.1:8152")
print(client.obj.add(1, 2))  # methods are exposed under the `obj.` prefix
```

A `GET /` on a running server returns the exposed function documentation.

## Test

```bash
python tests/test_rpc.py
```

Runs a stdlib HTTP server wrapping the parser and drives it with the built-in
client, covering positional/keyword args, nested calls, server exceptions and
method-not-found faults. No optional backend required.

To also verify a real backend end to end, run a server with `agreement="flask"`
(or any other) and call it with `ClientConnect`.

## Notes
- `_flask.py` / `_sanic.py` pass `_RPCParser_.obj` as the root object (matching
  the tornado backend) so `client.obj.<method>` resolves correctly.
- `_flask.py` falls back to a single threaded process on non-Linux platforms,
  since werkzeug only supports multi-process servers via `fork`.
