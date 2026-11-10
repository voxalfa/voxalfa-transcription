import os
import shutil
import subprocess

from argparse import ArgumentParser

from .lib.classifier import Classifier, format_labels
from .lib.svg import SVGVisitor, format_symbols
from .lib.fs import write_file
from .lib.types import time_signature
from .lib.html import HTMLVisitor, build_raw_text

DEPENDENCIES = ["pdftotext", "pdftocairo"]


def build_cli():
    cli = ArgumentParser(
        prog="pdf2vfa",
        description="PDF to vfa progressive conversion tool",
    )

    cli.add_argument("-i", "--input", required=True)
    cli.add_argument("-o", "--out-dir", default="./extracted")
    cli.add_argument("-t", "--time-signature", type=time_signature)
    cli.add_argument("-v", "--voices", type=int)
    cli.add_argument("-l", "--line-tolerance", type=float, default=4.0)
    cli.add_argument("-lg", "--line-gap", type=float, default=15.0)
    cli.add_argument("-wg", "--word-gap", type=float, default=5.0)
    cli.add_argument("-s", "--stroke-width", type=float, default=3.0)

    return cli


def main() -> int:
    args = build_cli().parse_args()

    for dep in DEPENDENCIES:
        if shutil.which(dep) is None:
            print(f"'{dep}' command is not executable")
            return 1

    if not os.path.exists(args.out_dir):
        os.mkdir(args.out_dir)

    # stage 1: Row extraction
    html_out = subprocess.run(
        ["pdftotext", args.input, "-bbox", "-"], stdout=subprocess.PIPE
    )

    html = html_out.stdout.decode()
    html_visitor = HTMLVisitor(args)
    pages = html_visitor.resolve_pages(html)
    raw_text, text_pages = build_raw_text(args, pages)

    write_file("raw.txt", raw_text, args)

    # stage 2: Symbol extraction
    svg_out = subprocess.run(
        ["pdftocairo", args.input, "-svg", "-"], stdout=subprocess.PIPE
    )

    svg = svg_out.stdout.decode()
    svg_visitor = SVGVisitor(args)
    symbols = svg_visitor.resolve_symbols(svg)
    symbols_dump = format_symbols(symbols)

    write_file("symbols.txt", symbols_dump, args)

    # stage 3: Row classification
    classifier = Classifier(args)
    labeled_pages = classifier.resolve_labels(text_pages)
    labels_dump = format_labels(text_pages, labeled_pages)

    write_file("labels.txt", labels_dump, args)

    # stage 4: Symbol merging
    # stage 5: Note tokenization
    # stage 6: Section arrangment
    # stage 7: Marker mapping (optional)
    # stage 8: Lyrics mapping (optional)
    # stage 9: Validation

    return 0


if __name__ == "__main__":
    SystemExit(main())
