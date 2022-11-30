from idom.config import IDOM_DEBUG_MODE


def test_idom_debug_mode_toggle():
    # just check that nothing breaks
    IDOM_DEBUG_MODE.current = True
    IDOM_DEBUG_MODE.current = False
