#!/bin/python3

"""
A CLI tool to help agents transcribing PDF files, mainly from solfa.mg to a voxalfa source file (.vfa)

usage: pdf2vfa [-h] -i INPUT [-o OUT_DIR] [-t TIME_SIGNATURE] [-v VOICES]
               [-T LINE_TOLERANCE]

options:
  -h, --help
  -i, --input INPUT
  -o, --out-dir OUT_DIR
  -t, --time-signature TIME_SIGNATURE
  -v, --voices VOICES
  -T, --line-tolerance LINE_TOLERANCE
"""

import os
import subprocess

from html.parser import HTMLParser
from argparse import ArgumentParser
from dataclasses import dataclass
from typing import List, Optional, Tuple


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


class HTMLVisitor(HTMLParser):
    pages: List[List[Word]]
    args: Args

    def __init__(self, args) -> None:
        super().__init__()
        self.pages = []
        self.stack = []
        self.args = args

    def handle_starttag(self, tag, attrs):
        self.stack.append(tag)

        if tag == "page":
            self.pages.append([])

        if tag == "word":
            word = Word(
                x1=self.float_attr(attrs[0]),
                y1=self.float_attr(attrs[1]),
                x2=self.float_attr(attrs[2]),
                y2=self.float_attr(attrs[3]),
                text="",
            )

            self.pages[-1].append(word)

    def handle_endtag(self, tag):
        self.stack.pop()

    def handle_data(self, data):
        if len(self.stack) > 0 and self.stack[-1] == "word":
            self.pages[-1][-1].text = data

    def resolve_pages(self, html: str) -> List[Page]:
        self.feed(html)

        pages = []

        for id, words in enumerate(self.pages):
            page = Page(id, rows=[])

            if len(words) == 0:
                continue

            words.sort(key=lambda w: w.y2)

            first = words[0]
            row = Row(baseline=first.y2, words=[first])

            for word in words[1:]:
                if word.y2 - self.args.line_tolerance > row.baseline:
                    row.words.sort(key=lambda w: w.x1)
                    page.rows.append(row)
                    row = Row(baseline=word.y2, words=[word])
                else:
                    row.words.append(word)

            pages.append(page)

        return pages

    def float_attr(self, s: Tuple[str, str | None]):
        return float(s[1] or "-1.0")


def dump_raw_text(out_dir: str, pages: List[Page]):
    file_path = os.path.join(out_dir, "raw.txt")

    with open(file_path, "+w") as file:
        for id, page in enumerate(pages):
            file.write(
                f"{"\n" if id > 0 else ""}--------------- Page {id} ---------------\n\n"
            )

            for row in page.rows:
                fixed_baseline = "%.3f" % row.baseline
                padded_baseline = fixed_baseline.rjust(7).replace(" ", "0")
                text = f"[{padded_baseline}] " + str.join(
                    " ", map(lambda w: w.text, row.words)
                )
                file.write(text + "\n")


@dataclass()
class Header:
    title: Optional[str] = None
    author: Optional[str] = None
    composer: Optional[str] = None
    tempo: Optional[str | int] = None
    key: Optional[str] = None


class RowClassifier:
    pages: List[Page]
    header: Header
    args: Args

    def __init__(self, pages: List[Page], args) -> None:
        self.pages = pages
        self.args = args
        self.header = Header()

    def process(self):
        for id, page in enumerate(self.pages):
            self.process_page(id, page)

    def process_page(self, page_id: int, page: Page):
        for row_id, row in enumerate(page.rows):
            pass

    def get_solfa_score(self, row: Row):
        pass

    def get_marker_score(self, row: Row):
        pass

    def stringify_row(self, row: Row):
        return str.join(" ", map(lambda w: w.text, row.words))


class Args:
    voices: Optional[int]
    time_signature: Optional[TimeSignature]
    line_tolerance: float


cli = ArgumentParser(
    prog="pdf2vfa",
    description="PDF to vfa conversion helper for agentic transcription",
)


cli.add_argument("-i", "--input", required=True)
cli.add_argument("-o", "--out-dir", default="./extracted")
cli.add_argument("-t", "--time-signature", type=time_signature)
cli.add_argument("-v", "--voices", type=int)
cli.add_argument("-T", "--line-tolerance", type=float, default=3.0)


args = cli.parse_args()


if not os.path.exists(args.out_dir):
    os.mkdir(args.out_dir)

cmd_out = subprocess.run(
    ["pdftotext", args.input, "-bbox", "-"], stdout=subprocess.PIPE
)

html = cmd_out.stdout.decode()

# stage 1: Row extraction
visitor = HTMLVisitor(args)
pages = visitor.resolve_pages(html)

dump_raw_text(args.out_dir, pages)

# stage 2: Row classification
classifier = RowClassifier(pages, args)
