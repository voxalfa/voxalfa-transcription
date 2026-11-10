import os
import glob
import logging
import shutil

from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor

from .lib.types import log_level, time_signature
from .lib.pipeline import process_file
from .lib.utils import logger

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
    cli.add_argument("-l", "--line-tolerance", type=float, default=6.0)
    cli.add_argument("-lg", "--line-gap", type=float, default=15.0)
    cli.add_argument("-wg", "--word-gap", type=float, default=5.0)
    cli.add_argument("-s", "--stroke-width", type=float, default=3.0)
    cli.add_argument("-L", "--log-level", type=log_level, default=logging.INFO)
    cli.add_argument("-j", "--jobs", type=int, default=os.cpu_count())

    return cli


def main() -> int:
    args = build_cli().parse_args()

    for dep in DEPENDENCIES:
        if shutil.which(dep) is None:
            logger.error(f"'{dep}' command is required but is not executable")
            return 1

    if not os.path.exists(args.out_dir):
        os.mkdir(args.out_dir)

    if not os.path.exists(args.input):
        logger.error(f"{args.input} is not accessible")
        return 1

    if os.path.isfile(args.input):
        files = [args.input]
    else:
        files = glob.glob(os.path.join(args.input, "*.pdf"))

    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        pool.map(process_file, files, [args for _ in files])

    return 0


if __name__ == "__main__":
    SystemExit(main())
