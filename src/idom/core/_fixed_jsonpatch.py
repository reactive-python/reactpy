# type: ignore

"""A patched version of jsonpatch

We need this because of: https://github.com/stefankoegl/python-json-patch/issues/138

The core of this patch is in `DiffBuilder._item_removed`. The rest is just boilerplate
that's been copied over with little to no changes.
"""

from jsonpatch import _ST_REMOVE
from jsonpatch import DiffBuilder as _DiffBuilder
from jsonpatch import JsonPatch as _JsonPatch
from jsonpatch import RemoveOperation, _path_join, basestring
from jsonpointer import JsonPointer


def apply_patch(doc, patch, in_place=False, pointer_cls=JsonPointer):
    if isinstance(patch, basestring):
        patch = JsonPatch.from_string(patch, pointer_cls=pointer_cls)
    else:
        patch = JsonPatch(patch, pointer_cls=pointer_cls)
    return patch.apply(doc, in_place)


def make_patch(src, dst, pointer_cls=JsonPointer):
    return JsonPatch.from_diff(src, dst, pointer_cls=pointer_cls)


class JsonPatch(_JsonPatch):
    @classmethod
    def from_diff(
        cls,
        src,
        dst,
        optimization=True,
        dumps=None,
        pointer_cls=JsonPointer,
    ):
        json_dumper = dumps or cls.json_dumper
        builder = DiffBuilder(src, dst, json_dumper, pointer_cls=pointer_cls)
        builder._compare_values("", None, src, dst)
        ops = list(builder.execute())
        return cls(ops, pointer_cls=pointer_cls)


class DiffBuilder(_DiffBuilder):
    def _item_removed(self, path, key, item):
        new_op = RemoveOperation(
            {
                "op": "remove",
                "path": _path_join(path, key),
            }
        )
        new_index = self.insert(new_op)
        self.store_index(item, new_index, _ST_REMOVE)
