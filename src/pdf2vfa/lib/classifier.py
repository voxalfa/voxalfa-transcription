import re

from typing import List
from .types import LabeledPage, Params, RowLabel, TextPage

DYNAMICS_RE = re.compile(r"(?<!\w)(?:ppp|pp|p|mp|mf|ff|fff)(?!\w)", re.IGNORECASE)
JUMP_RE = re.compile(r"D\.?[CS]\.?\d?", re.IGNORECASE)
MARKER_RE = re.compile(r"Fine|Fin|Farany", re.IGNORECASE)
TIME_RE = re.compile(r"(\d+)\s*/\s*(\d+)")
TEMPO_RE = re.compile(r"(rit|rall|accel|\d{2,3})", re.IGNORECASE)


class Classifier:
    text_pages: List[TextPage]
    params: Params

    def __init__(
        self,
        params,
    ) -> None:
        self.pamas = params

    def resolve_labels(self, text_pages: List[TextPage]) -> List[LabeledPage]:
        labels = []

        for page in text_pages:
            current = LabeledPage(page.id, [])

            for row_id, text in enumerate(page.rows):
                label = self.evaluate_row(row_id, text, current.rows)
                current.rows.append(label)

            labels.append(current)

        return labels

    def evaluate_row(self, id: int, text: str, context: List[RowLabel]):
        if len(text) == 0:
            return RowLabel.UNKNOWN

        if id == 0:
            return RowLabel.TITLE  # safe to assume?
        if id in range(1, 3) and self.is_meta_row(text):
            return RowLabel.META
        if self.is_solfa_row(text):
            return RowLabel.SOLFA
        if self.is_author_row(text, context[-1]):
            return RowLabel.AUTHOR
        if self.is_lyrics_row(text, context[-1]):
            return RowLabel.LYRICS
        if self.is_marker_row(text):
            return RowLabel.MARKER
        if self.is_extra_verse_row(text, context[-1]):
            return RowLabel.VERSE

        return RowLabel.UNKNOWN

    def is_author_row(self, text: str, prev: RowLabel):
        return prev == RowLabel.TITLE

    def is_meta_row(self, text: str):
        key = re.match(".*D[oô].*[ABCDEFG][b#]?.*", text)
        time_signature = re.match(".*\\d/\\d.*", text)
        return key != None or time_signature != None

    def is_marker_row(self, text: str):
        return bool(
            DYNAMICS_RE.search(text)
            or JUMP_RE.search(text)
            or TIME_RE.search(text)
            or TEMPO_RE.search(text)
            or MARKER_RE.search(text)
        )

    def is_solfa_row(self, text: str):
        return "|" in text or ":" in text

    def is_lyrics_row(self, text: str, prev: RowLabel):
        return prev == RowLabel.SOLFA

    def is_extra_verse_row(self, text, prev: RowLabel):
        return prev == RowLabel.LYRICS or prev == RowLabel.VERSE


def format_labels(text_pages: List[TextPage], labeled_pages: List[LabeledPage]):
    buffer = ""

    for page in text_pages:
        page_index = page.id + 1
        buffer += f"{"\n" if page_index > 1 else ""}>>>>>>>>> Page {page_index}\n\n"
        current = labeled_pages[page.id]

        for text_id, text in enumerate(page.rows):
            label = str(current.rows[text_id]).removeprefix("RowLabel.")
            buffer += f"{label:7} -> {text}\n"

    return buffer
