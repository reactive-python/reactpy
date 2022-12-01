from idom.core.vdom import make_vdom_constructor


__all__ = (
    "a",
    "animate",
    "animate_motion",
    "animate_transform",
    "circle",
    "clip_path",
    "defs",
    "desc",
    "discard",
    "ellipse",
    "fe_blend",
    "fe_color_matrix",
    "fe_component_transfer",
    "fe_composite",
    "fe_convolve_matrix",
    "fe_diffuse_lighting",
    "fe_displacement_map",
    "fe_distant_light",
    "fe_drop_shadow",
    "fe_flood",
    "fe_func_a",
    "fe_func_b",
    "fe_func_g",
    "fe_func_r",
    "fe_gaussian_blur",
    "fe_image",
    "fe_merge",
    "fe_merge_node",
    "fe_morphology",
    "fe_offset",
    "fe_point_light",
    "fe_specular_lighting",
    "fe_spot_light",
    "fe_tile",
    "fe_turbulence",
    "filter",
    "foreign_object",
    "g",
    "hatch",
    "hatchpath",
    "image",
    "line",
    "linear_gradient",
    "marker",
    "mask",
    "metadata",
    "mpath",
    "path",
    "pattern",
    "polygon",
    "polyline",
    "radial_gradient",
    "rect",
    "script",
    "set",
    "stop",
    "style",
    "svg",
    "switch",
    "symbol",
    "text",
    "text_path",
    "title",
    "tspan",
    "use",
    "view",
)

a = make_vdom_constructor("a")
animate = make_vdom_constructor("animate", allow_children=False)
animate_motion = make_vdom_constructor("animateMotion", allow_children=False)
animate_transform = make_vdom_constructor("animateTransform", allow_children=False)
circle = make_vdom_constructor("circle", allow_children=False)
clip_path = make_vdom_constructor("clipPath")
defs = make_vdom_constructor("defs")
desc = make_vdom_constructor("desc", allow_children=False)
discard = make_vdom_constructor("discard", allow_children=False)
ellipse = make_vdom_constructor("ellipse", allow_children=False)
fe_blend = make_vdom_constructor("feBlend", allow_children=False)
fe_color_matrix = make_vdom_constructor("feColorMatrix", allow_children=False)
fe_component_transfer = make_vdom_constructor(
    "feComponentTransfer", allow_children=False
)
fe_composite = make_vdom_constructor("feComposite", allow_children=False)
fe_convolve_matrix = make_vdom_constructor("feConvolveMatrix", allow_children=False)
fe_diffuse_lighting = make_vdom_constructor("feDiffuseLighting", allow_children=False)
fe_displacement_map = make_vdom_constructor("feDisplacementMap", allow_children=False)
fe_distant_light = make_vdom_constructor("feDistantLight", allow_children=False)
fe_drop_shadow = make_vdom_constructor("feDropShadow", allow_children=False)
fe_flood = make_vdom_constructor("feFlood", allow_children=False)
fe_func_a = make_vdom_constructor("feFuncA", allow_children=False)
fe_func_b = make_vdom_constructor("feFuncB", allow_children=False)
fe_func_g = make_vdom_constructor("feFuncG", allow_children=False)
fe_func_r = make_vdom_constructor("feFuncR", allow_children=False)
fe_gaussian_blur = make_vdom_constructor("feGaussianBlur", allow_children=False)
fe_image = make_vdom_constructor("feImage", allow_children=False)
fe_merge = make_vdom_constructor("feMerge", allow_children=False)
fe_merge_node = make_vdom_constructor("feMergeNode", allow_children=False)
fe_morphology = make_vdom_constructor("feMorphology", allow_children=False)
fe_offset = make_vdom_constructor("feOffset", allow_children=False)
fe_point_light = make_vdom_constructor("fePointLight", allow_children=False)
fe_specular_lighting = make_vdom_constructor("feSpecularLighting", allow_children=False)
fe_spot_light = make_vdom_constructor("feSpotLight", allow_children=False)
fe_tile = make_vdom_constructor("feTile", allow_children=False)
fe_turbulence = make_vdom_constructor("feTurbulence", allow_children=False)
filter = make_vdom_constructor("filter", allow_children=False)
foreign_object = make_vdom_constructor("foreignObject", allow_children=False)
g = make_vdom_constructor("g")
hatch = make_vdom_constructor("hatch", allow_children=False)
hatchpath = make_vdom_constructor("hatchpath", allow_children=False)
image = make_vdom_constructor("image", allow_children=False)
line = make_vdom_constructor("line", allow_children=False)
linear_gradient = make_vdom_constructor("linearGradient", allow_children=False)
marker = make_vdom_constructor("marker")
mask = make_vdom_constructor("mask")
metadata = make_vdom_constructor("metadata", allow_children=False)
mpath = make_vdom_constructor("mpath", allow_children=False)
path = make_vdom_constructor("path", allow_children=False)
pattern = make_vdom_constructor("pattern")
polygon = make_vdom_constructor("polygon", allow_children=False)
polyline = make_vdom_constructor("polyline", allow_children=False)
radial_gradient = make_vdom_constructor("radialGradient", allow_children=False)
rect = make_vdom_constructor("rect", allow_children=False)
script = make_vdom_constructor("script", allow_children=False)
set = make_vdom_constructor("set", allow_children=False)
stop = make_vdom_constructor("stop", allow_children=False)
style = make_vdom_constructor("style", allow_children=False)
svg = make_vdom_constructor("svg")
switch = make_vdom_constructor("switch")
symbol = make_vdom_constructor("symbol")
text = make_vdom_constructor("text", allow_children=False)
text_path = make_vdom_constructor("textPath", allow_children=False)
title = make_vdom_constructor("title", allow_children=False)
tspan = make_vdom_constructor("tspan", allow_children=False)
use = make_vdom_constructor("use", allow_children=False)
view = make_vdom_constructor("view", allow_children=False)
