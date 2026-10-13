import collections
from json import dumps as dumps
from json import loads as loads

library = collections.namedtuple("library", ["dumps", "loads"])(dumps, loads)


def updateParser(_RPCParser_):
    _RPCParser_.content_type = "application/json-rpc"
    _RPCParser_.library = library


def updateClient(ClientBase):
    ClientBase.library = library
