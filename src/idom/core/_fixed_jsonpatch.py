"""A patched version of jsonpatch

We need this because of: https://github.com/stefankoegl/python-json-patch/issues/138

The core of this patch is in `DiffBuilder._item_removed`. The rest is just boilerplate
that's been copied over with little to no changes.
"""

from jsonpatch import _ST_REMOVE
from jsonpatch import DiffBuilder as _DiffBuilder
from jsonpatch import JsonPatch as _JsonPatch
from jsonpatch import RemoveOperation, _path_join


def apply_patch(doc, patch, in_place=False):
    if isinstance(patch, (str, bytes)):
        patch = JsonPatch.from_string(patch)
    else:
        patch = JsonPatch(patch)
    return patch.apply(doc, in_place)


def make_patch(src, dst):
    return JsonPatch.from_diff(src, dst)


class JsonPatch(_JsonPatch):
    @classmethod
    def from_diff(cls, src, dst, optimization=True):
        builder = DiffBuilder()
        builder._compare_values("", None, src, dst)
        ops = list(builder.execute())
        return cls(ops)


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
