from typing import TYPE_CHECKING

from reactpy import component

if TYPE_CHECKING:
    from .load_second import child


@component
def root():
    return child()
