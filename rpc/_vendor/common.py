def pipInstallAndImport(package):
    try:
        return __import__(package)
    except ImportError:
        pipInstall(package)
        return __import__(package)


def pipInstall(package):
    import pip

    pip.main(["install", "-U", package])
