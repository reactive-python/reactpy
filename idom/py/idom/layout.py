import asyncio
import inspect


def element(function):

    def constructor(*args, **kwargs):
        return Element(function).update(*args, **kwargs)

    return constructor


class Element:

    __slots__ = (
        "_function",
        "_layout",
        "_state",
    )

    def __init__(self, function):
        self._function = function
        self._state = {}
        self._layout = None

    def mount(self, layout):
        self._layout = layout

    def update(self, *args, **kwargs):
        sig = inspect.signature(self._function)
        bound = sig.bind_partial(None, *args, **kwargs).arguments
        self._state.update(list(bound.items())[1:])
        if self._layout is not None:
            self._layout.update(self)
        return self

    async def render(self):
        model = self._function(self, **self._state)
        if inspect.isawaitable(model):
            model = await model
        return model

    def _iter_elements(self, model):
        if isinstance(model, dict):
            if isinstance(model["children"], (list, tuple)):
                for child in model.get("children", []):
                    if isinstance(child, Element):
                        yield child
                    else:
                        yield from self._inner_elements(child)

    def __repr__(self):
        state = ", ".join("%s=%s" % i for i in self._state.items())
        return "%s(%s)" % (self._function.__qualname__, state)


class Layout:

    def __init__(self, root):
        self._changed = asyncio.Event()
        self._root = id(root)
        self._state = {}
        self._updates = []
        self._create_element_state(id(root), None)
        self.update(root)

    @property
    def root(self):
        return self._root

    async def changed(self):
        await self._changed.wait()
        self._changed.clear()

    async def handle(self, target, handler, data):
        model_state = self._state[int(target)]
        function = model_state["event_handlers"][handler]
        result = function(data)
        if inspect.isawaitable(result):
            await result

    def update(self, element):
        self._updates.append(element)
        self._changed.set()

    async def render(self):
        changes = {}
        for element in self._updates:
            parent = self._state[id(element)]["parent"]
            async for eid, model in self._render_element(element, parent):
                changes[eid] = model
        self._updates.clear()
        return changes

    async def _render_element(self, element, parent_eid):
        element.mount(self)
        model = await element.render()

        eid = id(element)
        if self._has_element_state(eid):
            self._reset_element_state(eid)
        else:
            self._create_element_state(eid, parent_eid)

        async for i, m in self._render_model(model, eid):
            yield i, m

    async def _render_model(self, model, eid):
        index = 0
        to_visit = [model]
        while index < len(to_visit):
            node = to_visit[index]
            if isinstance(node, Element):
                async for i, m in self._render_element(node, eid):
                    yield i, m
            elif isinstance(node, dict):
                if "children" in node:
                    value = node["children"]
                    if isinstance(value, (list, tuple)):
                        to_visit.extend(value)
                    elif isinstance(value, (dict, Element)):
                        to_visit.append(value)
            index += 1
        yield eid, self._load_model(model, eid)

    def _load_model(self, model, eid):
        model = model.copy()
        model["children"] = self._load_model_children(
            model.setdefault("children", []), eid
        )
        model["eventHandlers"] = self._load_event_handlers(
            model.setdefault("eventHandlers", {}), eid
        )
        return model

    def _load_model_children(self, children, eid):
        if not isinstance(children, (list, tuple)):
            children = [children]
        loaded_children = []
        for child in children:
            if isinstance(c, dict):
                child = {
                    "type": "obj",
                    "data": self._load_model(child, eid),
                }
            elif isinstance(child, Element):
                child = {
                    "type": "ref",
                    "data": str(id(child)),
                }
            else:
                child = {
                    "type": "str",
                    "data": str(child),
                }
            loaded_children.append(child)
        return loaded_children

    def _has_element_state(self, eid):
        return eid in self._state

    def _create_element_state(self, eid, parent_eid):
        if self._has_element_state(parent_eid):
            self._state[parent_eid]["inner_elements"].add(eid)
        self._state[eid] = {
            "parent": parent_eid,
            "inner_elements": set(),
            "event_handlers": {},
        }

    def _reset_element_state(self, eid):
        parent_eid = self._state[eid]["parent"]
        self._delete_element_state(eid)
        self._create_element_state(eid, parent_eid)

    def _delete_element_state(self, eid):
        old = self._state.pop(eid)
        parent_eid = old["parent"]
        if self._has_element_state(parent_eid):
            self._state[parent_eid]["inner_elements"].remove(eid)
        for i in old["inner_elements"]:
            self._delete_element_state(i)

    def _load_event_handlers(self, handlers, key):
        event_targets = {}
        for event, handler in handlers.items():
            callback_key = "%s_%s" % (id(handler), event)
            event_targets[key] = callback_key
            self._state[key]["event_handlers"][callback_key] = handler
        return event_targets
