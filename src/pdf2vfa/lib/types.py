from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


@dataclass()
class Point:
    x: float
    y: float


@dataclass()
class Box:
    x1: float
    y1: float
    x2: float
    y2: float

    def merge(self, other: Box):
        return Box(
            max(self.x1, other.x1),
            max(self.y1, other.y1),
            max(self.x2, other.x2),
            max(self.y2, other.y2),
        )


@dataclass()
class Word:
    box: Box
    text: str


@dataclass()
class Row:
    baseline: float
    words: List[Word]


@dataclass()
class Page:
    id: int
    rows: List[Row]


@dataclass()
class TextPage:
    id: int
    rows: List[str]


class SVGPathKind(Enum):
    UNKNOWN = 0
    BARLINE = 1
    BARLINE2 = 2
    CURLY = 3
    FERMATA = 4
    STACCATO = 5
    MARCATO = 6
    CRESCENDO = 7
    DECRESCENDOJ = 8


@dataclass()
class SVGPath:
    kind: SVGPathKind
    box: Box
    points: List[Point]
    curved: bool


@dataclass()
class TimeSignature:
    top: int
    bottom: int


def time_signature(s: str):
    try:
        top, bottom = s.split("/")
        return TimeSignature(top=int(top), bottom=int(bottom))
    except:
        raise ValueError


class Params:
    out_dir: str
    voices: Optional[int]
    time_signature: Optional[TimeSignature]
    line_tolerance: float
    word_gap: float


@dataclass()
class Barline:
    x: float
    y1: float
    y2: float


@dataclass()
class Curly:
    x: float
    y1: float
    y2: float
