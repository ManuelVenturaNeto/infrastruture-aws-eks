from data_generator.utils import Options, Storage

from . import events, quotes


def ingest(storage: Storage, options: Options) -> int:
    files = quotes.generate(storage, options.start_year, options.end_year)
    events.generate_events(storage)
    return files
