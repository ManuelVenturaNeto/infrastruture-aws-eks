import argparse
import runpy
import sys
from pathlib import PurePosixPath


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("entrypoint", help="e.g. data_eng/stocks_b3/main.py")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    module = ".".join(PurePosixPath(args.entrypoint).with_suffix("").parts)
    sys.argv = [args.entrypoint, *args.args]
    runpy.run_module(module, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
