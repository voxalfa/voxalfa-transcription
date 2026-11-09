from html.parser import HTMLParser
from typing import List


class SVGVisitor(HTMLParser):
    stack: List[str]

    def __init__(self) -> None:
        super().__init__()
        self.stack = []

    def handle_starttag(self, tag, attrs):
        self.stack.append(tag)

    def handle_endtag(self, tag):
        self.stack.pop()
