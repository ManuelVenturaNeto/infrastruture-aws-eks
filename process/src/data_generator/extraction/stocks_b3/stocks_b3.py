from pathlib import Path

from data_generator.utils import Options

from . import events, quotes


def ingest(output_dir: Path, options: Options) -> int:
    files = quotes.generate(output_dir, options.start_year, options.end_year)
    events.generate_events(output_dir.with_name(f"{output_dir.name}_events"))
    return files
