import math

from html.parser import HTMLParser
from typing import List, Tuple

from .utils import format_float
from .types import Params, Page, Row, TextPage, Word, Box


class HTMLVisitor(HTMLParser):
    pages: List[List[Word]]
    args: Params

    def __init__(self, args) -> None:
        super().__init__()
        self.pages = []
        self.stack = []
        self.args = args

    def handle_starttag(self, tag, attrs):
        if tag == "page":
            self.pages.append([])

        if tag == "word":
            box = Box(
                x1=self.float_attr(attrs[0]),
                y1=self.float_attr(attrs[1]),
                x2=self.float_attr(attrs[2]),
                y2=self.float_attr(attrs[3]),
            )

            word = Word(box, text="")

            self.pages[-1].append(word)

        self.stack.append(tag)

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

            words.sort(key=lambda w: w.box.y2)

            first = words[0]
            row = Row(baseline=first.box.y2, words=[first])

            for word in words[1:]:
                if word.box.y2 - self.args.line_tolerance > row.baseline:
                    row.words.sort(key=lambda w: w.box.x1)
                    page.rows.append(row)
                    row = Row(baseline=word.box.y2, words=[word])
                else:
                    row.words.append(word)

            pages.append(page)

        return pages

    def float_attr(self, s: Tuple[str, str | None]):
        return float(s[1] or "-1.0")


def build_raw_text(args, pages: List[Page]) -> Tuple[str, List[TextPage]]:
    dump_text = ""
    text_pages = []

    for page in pages:
        left = min(
            (word.box.x1 for row in page.rows for word in row.words),
            default=0.0,
        )

        text_page = TextPage(page.id, rows=[])
        page_index = page.id + 1
        dump_text += f"{"\n" if page_index > 1 else ""}>>>>>>>>> Page {page}\n\n"
        last_y = -1

        for row in page.rows:
            first = row.words[0]
            indent = max(0, math.floor((first.box.x1 - left) / args.word_gap))

            row_text = " " * indent + first.text
            last_x = first.box.x2

            for word in row.words[1:]:
                if word.box.x1 < last_x:
                    row_text += word.text  # italic subscript edge case
                else:
                    space_count = max(
                        math.floor((word.box.x1 - last_x) / args.word_gap), 1
                    )
                    row_text += " " * space_count + word.text

                last_x = word.box.x2

            line_count = 1

            if last_y != -1:
                line_count = max(math.floor((row.baseline - last_y) / args.line_gap), 1)

            last_y = row.baseline
            dump_text += (
                f"[y={format_float(row.baseline)}] " + row_text + "\n" * line_count
            )

            text_page.rows.append(row_text)

        text_pages.append(text_page)

    return dump_text, text_pages
