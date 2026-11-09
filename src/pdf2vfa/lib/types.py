from dataclasses import dataclass
from typing import List, Optional


@dataclass()
class Word:
    x1: float
    y1: float
    x2: float
    y2: float
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
