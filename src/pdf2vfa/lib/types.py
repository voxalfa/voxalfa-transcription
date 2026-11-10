import logging

from dataclasses import dataclass
from enum import Enum
from math import log
from typing import List, Literal, Optional


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
            min(self.x1, other.x1),
            min(self.y1, other.y1),
            max(self.x2, other.x2),
            max(self.y2, other.y2),
        )

    def width(self):
        return self.x2 - self.x1

    def height(self):
        return self.y2 - self.y1


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


@dataclass()
class LabeledPage:
    id: int
    rows: List[RowLabel]


class RowLabel(Enum):
    TITLE = 0
    AUTHOR = 1
    META = 2
    MARKER = 3
    SOLFA = 4
    LYRICS = 5
    VERSE = 6
    NOTE = 7
    UNKNOWN = 8


class SVGPathKind(Enum):
    UNKNOWN = 0
    CURLY = 1
    BARLINE = 2
    UNDERLINE = 3
    HAIRPIN = 4
    FERMATA = 5
    MARCATO = 6
    STACCATO = 7


@dataclass()
class SVGPath:
    page: int
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
    line_gap: float
    word_gap: float
    stroke_width: float
    log_level: int


@dataclass()
class Header:
    title: str
    author: Optional[str]
    composer: Optional[str]
    key: str
    time_signature: Optional[TimeSignature]
    meter: Optional[str]
    tempo: Optional[str]


def log_level(s: str):
    level = logging._nameToLevel.get(s.upper())

    if level:
        return level
    else:
        raise ValueError
