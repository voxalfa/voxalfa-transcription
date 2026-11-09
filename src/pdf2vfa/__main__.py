import os
import shutil
import subprocess

from argparse import ArgumentParser

from .lib.fs import write_file
from .lib.types import time_signature
from .lib.html import HTMLVisitor, build_raw_text

DEPENDENCIES = ["pdftotext", "pdftocairo"]


def build_cli():
    cli = ArgumentParser(
        prog="pdf2vfa",
        description="PDF to vfa conversion helper for agentic transcription",
    )

    cli.add_argument("-i", "--input", required=True)
    cli.add_argument("-o", "--out-dir", default="./extracted")
    cli.add_argument("-t", "--time-signature", type=time_signature)
    cli.add_argument("-v", "--voices", type=int)
    cli.add_argument("-l", "--line-tolerance", type=float, default=3.0)
    cli.add_argument("-lg", "--line-gap", type=float, default=15.0)
    cli.add_argument("-wg", "--word-gap", type=float, default=5.0)

    return cli


def main() -> int:
    args = build_cli().parse_args()

    for dep in DEPENDENCIES:
        if shutil.which(dep) is None:
            print(f"'{dep}' command is not executable")
            return 1

    if not os.path.exists(args.out_dir):
        os.mkdir(args.out_dir)

    cmd_out = subprocess.run(
        ["pdftotext", args.input, "-bbox", "-"], stdout=subprocess.PIPE
    )

    html = cmd_out.stdout.decode()

    # stage 1: Row extraction
    visitor = HTMLVisitor(args)
    pages = visitor.resolve_pages(html)
    raw_text, rows = build_raw_text(args, pages)

    write_file("raw.txt", raw_text, args)

    # stage 2: Barline

    return 0


if __name__ == "__main__":
    SystemExit(main())
