Components With State
=====================

Components often need to change what’s on the screen as a result of an interaction. For
example, typing into the form should update the input field, clicking “next” on an image
carousel should change which image is displayed, clicking “buy” should put a product in
the shopping cart. Components need to “remember” things: the current input value, the
current image, the shopping cart. In IDOM, this kind of component-specific memory is
called state.
