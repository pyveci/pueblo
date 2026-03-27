# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "cli-fragments<1.3",
# ]
# ///

from cli_fragments import CliFragments  # ty: ignore[unresolved-import]

io = CliFragments()


def main():
    io.success("Hallo, Räuber Hotzenplotz.")
    return 42
