from functools import wraps

import idom


class RenderHistory(idom.StaticBunch):
    def __init__(self):
        classname = type(self).__name__
        self.__dict__[f"_{classname}__counters"] = {}
        self.__dict__[f"_{classname}__elements"] = set()

    def clear(self):
        for k in self.__dict__.items():
            if not k.startswith("_"):
                del self.__dict__[k]

    def track(self, name):
        if name.startswith("_"):
            raise ValueError(f"Name {name!r} startswith '_'.")

        self.__counters[name] = 0

        def setup(element_function):
            @wraps(element_function)
            def wrapper(*args, **kwargs):
                elmt = element_function(*args, **kwargs)
                if elmt.id not in self.__elements:
                    self.__elements.add(elmt.id)
                    self.__counters[name] += 1
                    self.__dict__[f"{name}_{self.__counters[name]}"] = elmt
                return elmt

            return wrapper

        return setup
