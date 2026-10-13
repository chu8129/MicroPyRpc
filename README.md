# rpc-service

Standalone JSON-RPC service, extracted from `core/utils/rpc/rpc` of the
`aigc_accelerator` project. The original local `core.utils` dependencies
(`decorator`, `config`, `log`, `common`) are vendored under `rpc/_vendor/`
so the package runs on its own.

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
print(client.add(1, 2))
```

A `GET /` on a running server returns the exposed function documentation.

## Notes

- The `tcp` (zeroMQ) backend is marked `TODO` in the original source.
- `core.utils.rpc.rpc` in the main repository is left untouched; this is a copy.
