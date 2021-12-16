from typing import Any, Dict, Sequence
from warnings import warn


def _wrap_in_warning_event_proxies(values: Sequence[Any]) -> Sequence[Any]:
    return [_EventProxy(x) if isinstance(x, dict) else x for x in values]


class _EventProxy(Dict[Any, Any]):
    def __getitem__(self, key: Any) -> Any:  # pragma: no cover
        try:
            return super().__getitem__(key)
        except KeyError:
            target = self.get("target")
            if isinstance(target, dict) and key in target:
                warn(
                    f"The event key event[{key!r}] has been moved event['target'][{key!r}",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return target[key]
            else:
                raise

    def get(self, key: Any, default: Any = None) -> Any:  # pragma: no cover
        try:
            return super().__getitem__(key)
        except KeyError:
            target = self.get("target")
            if isinstance(target, dict) and key in target:
                warn(
                    f"The event key event[{key!r}] has been moved event['target'][{key!r}",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return target[key]
            else:
                return default
