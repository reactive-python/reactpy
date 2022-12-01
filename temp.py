from idom import component


@component
def temp(x: int, y: int) -> None:
    return None


temp(*[1, 2])
