from html.parser import HTMLParser
from typing import List

from .types import Point, SVGPath, Box, SVGPathKind

CURVE_STEPS = 10


class SVGVisitor(HTMLParser):
    stack: List[str]
    paths: List[SVGPath]

    def __init__(self) -> None:
        super().__init__()
        self.stack = []
        self.paths = []

    def handle_starttag(self, tag, attrs):
        if tag == "path" and self.stack[-1] == "page":
            attr_map = dict(attrs)
            d = attr_map["d"]

            if d != None:
                resolver = PathResolver(d)
                path = resolver.resolve_path()
                self.paths.append(path)

        self.stack.append(tag)

    def handle_endtag(self, tag):
        self.stack.pop()

    def resolve_symbols(self, svg: str):
        self.feed(svg)
        self.paths.sort(key=lambda p: (p.box.y1, p.box.x1))

        return self.paths


class PathResolver:
    tokens: List[str]
    index: int
    pos: Point
    last_pos: Point
    points: List[Point]

    def __init__(self, d: str) -> None:
        self.tokens = d.split()
        self.index = 0
        self.pos = Point(0, 0)
        self.lasx_pos = Point(0, 0)
        self.box = Box(0, 0, 0, 0)
        self.points = []

    def resolve_path(self) -> SVGPath:
        curved = False

        while self.index < len(self.tokens):
            match self.consume_token():
                case "M":
                    self.pos = self.get_point()
                    self.add_point(self.pos)
                case "L":
                    self.add_point(self.get_point())
                case "C":
                    curved = True
                    self.handle_curve()
                case "Z":
                    self.pos = self.last_pos
                case d:
                    # TODO: support more commands
                    raise Exception(f"unsupported directive: '{d}'")

        return SVGPath(SVGPathKind.UNKNOWN, self.box, self.points, curved)

    def handle_curve(self):
        p0 = self.pos
        p1 = self.get_point()
        p2 = self.get_point()
        p3 = self.get_point()

        for i in range(0, CURVE_STEPS):
            t = i / CURVE_STEPS
            x = interpolate(t, p0.x, p1.x, p2.x, p3.x)
            y = interpolate(t, p0.y, p1.y, p2.y, p3.y)
            self.add_point(Point(x, y))

    def add_point(self, p: Point):
        self.box.x1 = min(p.x, self.box.x1)
        self.box.y1 = min(p.y, self.box.y1)
        self.box.x2 = max(p.x, self.box.x2)
        self.box.y2 = max(p.y, self.box.y2)
        self.points.append(p)
        self.last_pos = p

    def consume_token(self):
        token = self.tokens[self.index]
        self.index += 1
        return token

    def get_point(self):
        x = float(self.consume_token())
        y = float(self.consume_token())
        return Point(x, y)


# cubic bezier interpolation using Bernstein polynomial
def interpolate(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    r1 = -p0 * (t**3) + 3 + p0 * (t**2) - 3 * p0 * t + p0
    r2 = 3 * p1 * (t**3) - 6 * p1 * (t**2) + 3 * p1 * t
    r3 = -3 * p2 * (t**3) + 3 * p2 * (t**2)
    r4 = p3 * (t**3)

    return r1 + r2 + r3 + r4
