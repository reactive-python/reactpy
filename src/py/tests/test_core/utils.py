from functools import wraps


class RenderHistory:
    def __init__(self):
        self.__counters = {}
        self.__elements = set()

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
                    setattr(self, f"{name}_{self.__counters[name]}", elmt)
                return elmt

            return wrapper

        return setup
