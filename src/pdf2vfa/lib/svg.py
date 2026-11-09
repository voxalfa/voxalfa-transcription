import math

from html.parser import HTMLParser
from typing import List
from .utils import format_float
from .types import Params, Point, SVGPath, Box, SVGPathKind

CURVE_STEPS = 10


class SVGVisitor(HTMLParser):
    stack: List[str]
    paths: List[SVGPath]
    max_w: float
    max_h: float
    min_w: float
    min_h: float
    current_page: int
    params: Params

    def __init__(self, params) -> None:
        super().__init__()
        self.stack = []
        self.paths = []
        self.max_w = 0
        self.max_h = 0
        self.min_w = math.inf
        self.min_h = math.inf
        self.current_page = 0
        self.params = params

    def handle_starttag(self, tag, attrs):
        if tag == "path" and self.stack[-1] != "g":
            attr_map = dict(attrs)
            d = attr_map["d"]

            if d != None:
                resolver = PathResolver(d)
                path = resolver.resolve_path(self.current_page)

                self.max_w = max(self.max_w, path.box.width())
                self.min_w = min(self.min_w, path.box.width())
                self.max_h = max(self.max_h, path.box.height())
                self.min_h = min(self.min_h, path.box.height())

                self.paths.append(path)

        self.stack.append(tag)

    def handle_endtag(self, tag):
        self.stack.pop()

        if tag == "page":
            self.current_page += 1

    def resolve_symbols(self, svg: str):
        self.feed(svg)
        self.paths.sort(key=lambda p: (p.page, p.box.y1, p.box.x1))

        for path in self.paths:
            self.identify_symbol(path)

        return self.paths

    # TODO: find a good classification method for identifying other symbols
    def identify_symbol(self, path: SVGPath):
        w = path.box.width()
        h = path.box.height()
        sw = self.params.stroke_width

        if path.curved and w > sw and h > 40:
            path.kind = SVGPathKind.CURLY
        elif not path.curved and w < sw and h > 10:
            path.kind = SVGPathKind.BARLINE
        elif not path.curved and w > 20 and h < sw:
            path.kind = SVGPathKind.UNDERLINE
        else:
            path.kind = SVGPathKind.UNKNOWN


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
        self.box = Box(math.inf, math.inf, 0, 0)
        self.points = []

    def resolve_path(self, page: int) -> SVGPath:
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

        return SVGPath(
            page=page,
            kind=SVGPathKind.UNKNOWN,
            box=self.box,
            points=self.points,
            curved=curved,
        )

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
    r1 = -p0 * (t**3) + 3 * p0 * (t**2) - 3 * p0 * t + p0
    r2 = 3 * p1 * (t**3) - 6 * p1 * (t**2) + 3 * p1 * t
    r3 = -3 * p2 * (t**3) + 3 * p2 * (t**2)
    r4 = p3 * (t**3)

    return r1 + r2 + r3 + r4


def format_symbols(symbols: List[SVGPath]):
    buffer = ""

    for id, symbol in enumerate(symbols):
        box = symbol.box
        x1 = format_float(box.x1)
        y1 = format_float(box.y1)
        x2 = format_float(box.x2)
        y2 = format_float(box.y2)
        width = format_float(box.width())
        height = format_float(box.height())

        buffer += (
            f"[id={id}]"
            + f" page={symbol.page} kind={symbol.kind} x1={x1} y1={y1} x2={x2} y2={y2}"
            + f" / width={width} height={height}"
            + f" ({len(symbol.points)} points, curved={symbol.curved})\n"
        )

    return buffer
