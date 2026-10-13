import rpc


class MyServer:
    """Example RPC server object. Public methods are exposed over JSON-RPC."""

    def add(self, a, b):
        """Add two numbers."""
        return a + b

    def echo(self, value):
        """Echo back the given value."""
        return value


if __name__ == "__main__":
    import fire

    fire.Fire()
