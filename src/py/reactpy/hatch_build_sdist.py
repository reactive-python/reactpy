"""Custom sdist build hook for reactpy.

As defined in pyproject.toml, this script should automatically be executed
when creating a source (.tar.gz) distribution.

See also: https://hatch.pypa.io/1.9/plugins/build-hook/custom/

"""
import shutil
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        # https://github.com/pypa/hatch/issues/1197
        # As a workaround, delete js/node_modules/ so hatchling does not
        # mistakenly omit js/packages/ from the source distribution.
        #
        # If only the source distribution is built, i.e. by running one of:
        #   - `hatch build --target sdist`
        #   - `python -m build --sdist`
        # then node_modules/ will be missing. Developers that later want to run
        # `npm run build` will also need to reinstall with `npm ci`.
        modules = Path(self.root) / "js" / "node_modules"
        if modules.is_dir():
            print("Removing", modules)
            shutil.rmtree(modules)
