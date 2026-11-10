import os
import subprocess

from .classifier import Classifier, format_labels
from .svg import SVGVisitor, format_symbols
from .fs import write_file
from .html import HTMLVisitor, build_raw_text


def process_file(file_path: str, args):
    file_name = os.path.basename(file_path)
    base_name = file_name.removesuffix(".pdf")
    out_dir = os.path.join(args.out_dir, base_name)

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # stage 1: Row extraction
    html_out = subprocess.run(
        ["pdftotext", file_path, "-bbox", "-"], stdout=subprocess.PIPE
    )

    html = html_out.stdout.decode()
    html_visitor = HTMLVisitor(args)
    pages = html_visitor.resolve_pages(html)
    raw_text, text_pages = build_raw_text(args, pages)

    write_file("raw.txt", raw_text, out_dir)

    # stage 2: Symbol extraction
    svg_out = subprocess.run(
        ["pdftocairo", file_path, "-svg", "-"], stdout=subprocess.PIPE
    )

    svg = svg_out.stdout.decode()
    svg_visitor = SVGVisitor(args)
    symbols = svg_visitor.resolve_symbols(svg)
    symbols_dump = format_symbols(symbols)

    write_file("symbols.txt", symbols_dump, out_dir)

    # stage 3: Row classification
    classifier = Classifier(file_name, args)
    labeled_pages = classifier.resolve_labels(text_pages)
    labels_dump = format_labels(text_pages, labeled_pages)

    write_file("labels.txt", labels_dump, out_dir)

    # stage 4: Symbol merging
    # stage 5: Note tokenization
    # stage 6: Section arrangment
    # stage 7: Marker mapping (optional)
    # stage 8: Lyrics mapping (optional)
    # stage 9: Validation
