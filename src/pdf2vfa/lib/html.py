import math

from html.parser import HTMLParser
from typing import List, Tuple
from .types import Params, Page, Row, Word


class HTMLVisitor(HTMLParser):
    pages: List[List[Word]]
    args: Params

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


def build_raw_text(args, pages: List[Page]) -> Tuple[str, List[str]]:
    dump_text = ""
    rows = []

    for id, page in enumerate(pages):
        dump_text += f"{"\n" if id > 0 else ""}>>>>>>>>> Page {id}\n\n"

        left = min(
            (word.x1 for row in page.rows for word in row.words),
            default=0.0,
        )

        last_y = -1

        for row in page.rows:
            fixed_baseline = "%.2f" % row.baseline
            padded_baseline = fixed_baseline.rjust(7).replace(" ", "0")

            first = row.words[0]
            indent = max(0, math.floor((first.x1 - left) / args.word_gap))

            row_text = " " * indent + first.text
            last_x = first.x2

            for word in row.words[1:]:
                space_count = max(math.floor((word.x1 - last_x) / args.word_gap), 1)
                row_text += " " * space_count + word.text
                last_x = word.x2

            line_count = 1

            if last_y != -1:
                line_count = max(math.floor((row.baseline - last_y) / args.line_gap), 1)

            last_y = row.baseline
            dump_text += f"[{padded_baseline}] " + row_text + "\n" * line_count

            rows.append(row_text)

    return dump_text, rows
