from importlib import import_module

__all__ = []


for name in ["sanic"]:
    try:
        import_module(name)
    except ImportError:
        pass
    else:
        import_module(__name__ + "." + name)
        __all__.append(name)
