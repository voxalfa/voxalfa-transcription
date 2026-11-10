import logging

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)


def format_float(input: float):
    fixed = "%.2f" % input
    padded = fixed.rjust(6).replace(" ", "0")
    return padded
