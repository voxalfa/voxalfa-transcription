import logging
import re

from typing import List
from .utils import logger
from .types import LabeledPage, Params, RowLabel, TextPage

DYNAMICS_RE = re.compile(
    r"(?<!\w)(?:ppp|pp|mp|mf|ff|fff|p|f)(?![\w.'’,])", re.IGNORECASE
)
JUMP_RE = re.compile(r"(?<!\w)D\.?\s?[CS]\.?(?!\w)", re.IGNORECASE)
MARKER_RE = re.compile(r"(?<!\w)(?:Fine|Fin|\$|>|<)(?!\w)", re.IGNORECASE)
TIME_RE = re.compile(r"(?<![\d/])\d{1,2}\s*/\s*\d{1,2}(?![\d/])")
TEMPO_RE = re.compile(r"(?<!\w)(?:rit|rall|accel)(?!\w)", re.IGNORECASE)
KEY_RE = re.compile(r"D[oô]\s+dia", re.IGNORECASE)
NOTE_RE = re.compile(r"[smltdrf][aie]?[',]?")


class Classifier:
    file_name: str
    text_pages: List[TextPage]
    params: Params

    def __init__(
        self,
        file_name: str,
        params,
    ) -> None:
        self.file_name = file_name
        self.params = params

    def resolve_labels(self, text_pages: List[TextPage]) -> List[LabeledPage]:
        labels = []

        for page in text_pages:
            current = LabeledPage(page.id, [])

            for row_id, text in enumerate(page.rows):
                label = self.evaluate_row(row_id, text, current.rows)
                current.rows.append(label)

                if self.params.log_level >= logging.WARN and label == RowLabel.UNKNOWN:
                    prev_id = row_id - 1
                    prev = page.rows[prev_id]
                    prev_label = str(current.rows[prev_id]).removeprefix("RowLabel.")

                    logger.warning(
                        f"Unknown label in {self.file_name} (page {page.id + 1}, row: {row_id})\n"
                        + f"{prev_id} |   {prev.lstrip(" ") } [{prev_label}]\n"
                        + f"{row_id} |>> {text.lstrip(" ")}\n"
                    )

            labels.append(current)

        return labels

    def evaluate_row(self, id: int, text: str, context: List[RowLabel]):
        if len(text) == 0:
            return RowLabel.UNKNOWN

        if id == 0:
            return RowLabel.TITLE  # safe to assume?
        if self.is_meta_row(text):
            return RowLabel.META
        if self.is_solfa_row(text):
            return RowLabel.SOLFA
        if self.is_author_row(text, context[-1]):
            return RowLabel.AUTHOR
        if self.is_lyrics_row(text, context[-1]):
            return RowLabel.LYRICS
        if self.is_marker_row(text):
            return RowLabel.MARKER
        if self.is_verse_row(text, context[-1]):
            return RowLabel.VERSE
        if self.is_note_row(text, context[-1]):
            return RowLabel.NOTE

        return RowLabel.UNKNOWN

    def is_author_row(self, text: str, prev: RowLabel):
        return prev == RowLabel.TITLE or prev == RowLabel.AUTHOR

    def is_meta_row(self, text: str):
        return KEY_RE.search(text) is not None

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

    def is_verse_row(self, text: str, prev: RowLabel):
        return prev == RowLabel.LYRICS or prev == RowLabel.VERSE

    def is_note_row(self, text: str, prev: RowLabel):
        tokens = text.split()
        return (
            prev == RowLabel.META
            and bool(tokens)
            and all(NOTE_RE.fullmatch(t) for t in tokens)
        )


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
