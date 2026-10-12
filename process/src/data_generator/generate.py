import argparse
import importlib
import logging
import pkgutil
from pathlib import Path

from data_generator import extraction
from data_generator.utils import Options

PROCESSES = sorted(module.name for module in pkgutil.iter_modules(extraction.__path__))

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=PROCESSES)
    parser.add_argument("--out", default="process/src/datasets")
    parser.add_argument("--files", type=int, default=400)
    parser.add_argument("--start_year", type=int)
    parser.add_argument("--end_year", type=int)
    args = parser.parse_args()

    output_dir = Path(args.out) / args.name / args.name
    output_dir.mkdir(parents=True, exist_ok=True)

    process = importlib.import_module(f"{extraction.__name__}.{args.name}")
    options = Options(
        files=args.files, start_year=args.start_year, end_year=args.end_year
    )
    files = process.ingest(output_dir, options)

    total_bytes = sum(f.stat().st_size for f in output_dir.rglob("*.parquet"))
    logger.info("done: %d files, %.2f GB", files, total_bytes / (1 << 30))


if __name__ == "__main__":
    main()
