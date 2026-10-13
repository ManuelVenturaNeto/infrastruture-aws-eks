from collections.abc import Callable
from pathlib import Path
from typing import BinaryIO

import pyarrow as pa
import pyarrow.csv
import pyarrow.parquet as pq


def csv_to_parquet(
    open_stream: Callable[[], BinaryIO],
    destination: Path,
    parse_options: pyarrow.csv.ParseOptions,
    read_options: pyarrow.csv.ReadOptions | None = None,
    null_values: list[str] | None = None,
) -> int:
    """Converts delimited text into a zstd parquet file with every column as string.

    Args:
        open_stream: Opens a fresh binary stream of the text. It is called
            twice: once to read the header and once to convert.
        destination: Parquet file to write; its folder is created if missing.
        parse_options: Delimiter and quoting of the text.
        read_options: Encoding and block size; pyarrow defaults when None.
        null_values: Strings read as null; pyarrow defaults when None.

    Returns:
        The number of rows written.
    """
    with open_stream() as stream:
        column_names = pyarrow.csv.open_csv(
            stream, read_options=read_options, parse_options=parse_options
        ).schema.names
    convert_options = pyarrow.csv.ConvertOptions(
        column_types={name: pa.string() for name in column_names},
        null_values=null_values,
    )
    rows = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open_stream() as stream:
        reader = pyarrow.csv.open_csv(
            stream,
            read_options=read_options,
            parse_options=parse_options,
            convert_options=convert_options,
        )
        with pq.ParquetWriter(destination, reader.schema, compression="zstd") as writer:
            for batch in reader:
                writer.write_batch(batch)
                rows += batch.num_rows
    return rows
