import logging
import uuid
from urllib.parse import splittype

from ._vendor.decorator import Timer


class Fault(object):
    def __init__(self, code=-32000, message="Server error", rpcid=None):
        self.faultCode = code
        self.faultString = message
        self.rpcid = rpcid

    def error(self):
        return {"code": self.faultCode, "message": self.faultString}

    def response(self, rpcid=None, version=None):
        if not version:
            version = ""
        if rpcid:
            self.rpcid = rpcid
        return __import__("json").dumps(self, methodresponse=True, rpcid=self.rpcid, version=version)

    def __repr__(self):
        return "<Fault %s: %s>" % (self.faultCode, self.faultString)

    def __call__(self, message=None):
        self.faultString = ", ".join([str(_) for _ in [self.faultString, message] if _])
        return self


class Faults(object):
    infoToCodeDict = {"parse_error": -32700, "method_not_found": -32601, "invalid_request": -32600, "invalid_params": -32602, "internal_error": -32603}
    messages = {}

    def __init__(self, *args):
        pass

    def __getattr__(self, attr):
        return Fault(self.infoToCodeDict[attr], self.messages.get(attr, " ".join(map(str.capitalize, attr.split("_")))))


class BaseRPCParser(object):
    content_type = "text/plain"
    library = None

    @property
    def faults(self):
        return Faults(self)

    def __init__(self):
        self.dumps, self.loads = self.library.dumps, self.library.loads

    def __call__(self, methodClassObject, request_body):
        try:
            requests, rawRequst = self.parseRequestBody(request_body)
        except Exception as e:
            logging.error(e, exc_info=True)
            return self.faults.parse_error(repr(e))

        return [(self.matchParametersAndRun(methodClassObject, request[0], request[1]), requests, rawRequst, index) for index, request in enumerate(requests)]

    def parseRequestBody(self, request_body):
        try:
            request = self.loads(request_body)
        except Exception as e:
            logging.error(e, exc_info=True)
            raise self.faults.parse_error(repr(e))
        request_list = [(request["method"], request.get("params", []))]

        return tuple(request_list), request

    def matchParametersAndRun(self, method, method_name, params):
        attr_tree = method_name.split(".")

        def _methodExist(attr_name, obj):
            if attr_name == "obj":
                return obj

            if attr_name.startswith("_"):
                raise AttributeError("Private object or method. start with:_")

            attr = getattr(obj, attr_name) if hasattr(obj, attr_name) else None

            if attr is None:
                raise AttributeError("Private object or method. no exists")

            if getattr(attr, "private", False):
                raise AttributeError("Private object or method. is private")

            return attr

        try:
            for attr_name in attr_tree:
                method = _methodExist(attr_name, method)
        except AttributeError:
            return self.faults.method_not_found()

        if not callable(method):
            return self.faults.method_not_found()

        if isinstance(params, dict):
            args, kwargs = [], params
        elif isinstance(params, (list, tuple)):
            args, kwargs = params, {}
        else:
            return self.faults.invalid_params()

        try:
            with Timer(f"RUN:{method.__qualname__ if hasattr(method, '__qualname__') else None} > {method_name}"):
                response = method(*args, **kwargs)

        except Exception as e:
            logging.error(e, exc_info=True)
            return self.faults.internal_error(repr(e))

        logging.info("response:%s" % type(response))

        if getattr(method, "async", False):
            if response is not None:
                return self.faults.internal_error()
        else:
            return response

    def serializationResponse(self, responses):
        if isinstance(responses, Fault):
            return self.dumps(dict(error=dict(code=responses.faultCode, message=responses.faultString)))

        if len(responses) and len(responses) != len(responses[0][1]):
            return self.dumps(dict(error=dict(code=1, message=self.faults.internal_error())))

        response_list = []
        for response, _, rawRequest, *_ in responses:
            rpcid = rawRequest["id"]
            params = dict(
                result=None if isinstance(response, Fault) else response,
                version="qw240423",
                rpcid=rpcid,
                methodresponse=True,
                status=bool(not isinstance(response, Fault)),
            )

            if isinstance(response, Fault):
                params["error"] = dict(code=response.faultCode, message=response.faultString)

            response_json = self.dumps(params)
            response_list.append(response_json)

        response_text = response_list[0] if response_list else ""
        assert isinstance(response_text, str)
        return response_text


def check_for_errors(result):
    if not result:
        return result
    if not isinstance(result, dict):
        raise TypeError("Response is not a dict.")
    if "result" not in result.keys() and "error" not in result.keys():
        raise ValueError("Response does not have a result or error key.")
    if "error" in result.keys() and result["error"] is not None:
        raise Exception((result["error"]["code"], result["error"]["message"]))
    return result


class _Method:
    def __init__(self, send, name):
        self.__send = send
        self.__name = name

    def __call__(self, *args, **kwargs):
        if len(args) > 0 and len(kwargs) > 0:
            raise RuntimeError("Cannot use both positional and keyword arguments " "(according to JSON-RPC spec.)")
        return self.__send(self.__name, args) if len(args) > 0 else self.__send(self.__name, kwargs)

    def __getattr__(self, name):
        return _Method(self.__send, "%s.%s" % (self.__name, name))

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.__name)

    def __str__(self):
        return self.__repr__()

    def __dir__(self):
        return self.__dict__.keys()


class ClientConnect:
    __version, library = "qw2304", None

    def __init__(self, uri=None, transport=None, encoding=None, verbose=0, version=None, timeout=3600):
        if splittype(uri)[0] not in ("http", "https"):
            raise IOError("Unsupported JSON-RPC protocol.")
        self.uri, self.timeout, self.__encoding = uri, timeout, encoding
        self.dumps, self.loads = self.library.dumps, self.library.loads

    def _request(self, methodname, params, rpcid=None):
        request = self.dumps(dict(params=params, method=methodname, encoding=self.__encoding, rpcid=rpcid, version=self.__version, id=str(uuid.uuid4())))
        response = self._onRequest(self.uri, data=request, timeout=self.timeout)

        if not response:
            return None

        response = self.loads(response)
        check_for_errors(response)
        return response["result"]

    def _onRequest(self, url, data, timeout=None):
        import requests

        # import zlib

        with Timer("rpc", debug=True):
            # return requests.post(url, data=zlib.compress(data.encode()), headers={'Content-Encoding': 'gzip, deflate'}, timeout=timeout).text
            return requests.post(url, data=data, timeout=timeout).text
            # return httpx.request("POST", url, data=data, timeout=timeout).text # 400ms

    def __getattr__(self, name):
        return _Method(self._request, name)

    def __repr__(self):
        return "<%s for %s%s>" % (self.__class__.__name__, self.__host, self.__handler)

    def __enter__(self):
        return self
