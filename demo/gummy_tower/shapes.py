"""Gummy animal silhouettes, shared by the physics sim and the Blender renderer.

Each animal is a set of convex parts (ellipses / polygons) in the XZ plane, extruded along Y.
The union of the parts is the visible outline; each part is one convex collision hull.
"""
import math
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely import affinity

THICK = 0.42      # extrusion thickness (y), bevel adds a bit more visually

def ell(cx, cz, rx, rz, rot=0.0):
    return ("ell", cx, cz, rx, rz, rot)

def tri(*pts):
    return ("poly", pts)

# ---- the "cute" theme (all roughly 1 unit tall) -------------------------------------
ANIMALS = {
    "cat": {
        "parts": [ell(0, 0, 0.44, 0.34), ell(0, 0.42, 0.33, 0.28),
                  tri((-0.32, 0.5), (-0.27, 0.86), (-0.06, 0.66)),
                  tri((0.32, 0.5), (0.27, 0.86), (0.06, 0.66)),
                  ell(0.42, 0.12, 0.09, 0.24, -0.5)],
        "eyes": [(-0.12, 0.45), (0.12, 0.45)], "nose": (0, 0.36),
    },
    "bunny": {
        "parts": [ell(0, 0, 0.4, 0.34), ell(0, 0.4, 0.28, 0.25),
                  ell(-0.12, 0.83, 0.085, 0.27, 0.12), ell(0.12, 0.83, 0.085, 0.27, -0.12),
                  ell(-0.4, -0.08, 0.12, 0.12)],
        "eyes": [(-0.1, 0.44), (0.1, 0.44)], "nose": (0, 0.35),
    },
    "panda": {
        "parts": [ell(0, 0, 0.5, 0.38), ell(0, 0.44, 0.36, 0.3),
                  ell(-0.27, 0.69, 0.12, 0.11), ell(0.27, 0.69, 0.12, 0.11),
                  ell(-0.42, -0.2, 0.15, 0.13), ell(0.42, -0.2, 0.15, 0.13)],
        "eyes": [(-0.13, 0.47), (0.13, 0.47)], "nose": (0, 0.37),
    },
    "penguin": {
        "parts": [ell(0, 0.12, 0.32, 0.56), ell(-0.34, 0.12, 0.1, 0.26, -0.35),
                  ell(0.34, 0.12, 0.1, 0.26, 0.35), ell(-0.14, -0.44, 0.13, 0.06),
                  ell(0.14, -0.44, 0.13, 0.06)],
        "eyes": [(-0.1, 0.42), (0.1, 0.42)], "nose": (0, 0.32),
    },
    "dog": {
        "parts": [ell(0, 0, 0.45, 0.34), ell(0, 0.42, 0.3, 0.27),
                  ell(-0.3, 0.38, 0.1, 0.22, 0.3), ell(0.3, 0.38, 0.1, 0.22, -0.3),
                  ell(0.44, 0.16, 0.07, 0.17, -0.6)],
        "eyes": [(-0.11, 0.46), (0.11, 0.46)], "nose": (0, 0.35),
    },
}

def part_polygon(p, n=40):
    if p[0] == "ell":
        _, cx, cz, rx, rz, rot = p
        poly = Polygon([(rx * math.cos(2 * math.pi * k / n), rz * math.sin(2 * math.pi * k / n))
                        for k in range(n)])
        poly = affinity.rotate(poly, rot, origin=(0, 0), use_radians=True)
        return affinity.translate(poly, cx, cz)
    return Polygon(p[1])

def animal_geometry(name):
    """Returns (outline polygon, list of convex part polygons, eyes, nose), centred on the
    outline's centroid so the body origin is its centre of mass."""
    a = ANIMALS[name]
    parts = [part_polygon(p) for p in a["parts"]]
    outline = unary_union(parts).buffer(0.0)
    c = outline.centroid
    shift = lambda g: affinity.translate(g, -c.x, -c.y)
    outline = shift(outline)
    parts = [shift(p) for p in parts]
    eyes = [(x - c.x, z - c.y) for x, z in a["eyes"]]
    nose = (a["nose"][0] - c.x, a["nose"][1] - c.y)
    return outline, parts, eyes, nose

GUMMY_COLORS = {
    "strawberry": (0.95, 0.04, 0.07),
    "orange": (1.0, 0.32, 0.02),
    "lemon": (1.0, 0.78, 0.04),
    "lime": (0.32, 0.85, 0.06),
    "blueberry": (0.06, 0.32, 1.0),
    "grape": (0.5, 0.1, 0.75),
    "pink": (1.0, 0.28, 0.5),
    "clear": (0.97, 0.93, 0.85),
}
