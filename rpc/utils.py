def collectInfo(self):
    from ._vendor.config import TerminalColor

    strings = []

    from ._vendor.common import pipInstallAndImport

    objgraph = pipInstallAndImport("objgraph")
    strings.append(f"\n{TerminalColor.BLUE}objgraph:{TerminalColor.RESET}\n\n")
    # objgraph.show_growth()
    # objgraph.show_refs([self], filename="/tmp/python.memory.objgraph.png")

    strings.append(f"\n{TerminalColor.BLUE}functions:{TerminalColor.RESET}\n\n")
    key = "obj"
    obj = getattr(self, key)
    info = {method: getattr(obj, method).__doc__ for method in dir(obj) if (not method.startswith("_")) and callable(getattr(obj, method))}
    string = "\n".join(["{:<50} {:<80}".format(".".join(("rpcObject", key, func)), str(doc).strip()) for func, doc in info.items()])
    strings.append("\n%s\n" % string)

    return "\n".join(strings)
