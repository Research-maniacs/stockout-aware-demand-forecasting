"""Print the first 50 rows of data/train.parquet."""

from pathlib import Path

import pyarrow.parquet as pq


ROW_LIMIT = 50
PARQUET_FILE = Path(__file__).resolve().parents[1] / "data" / "train.parquet"


def main() -> None:
    """Read one small batch from the Parquet file and print it as a table."""
    if not PARQUET_FILE.is_file():
        raise FileNotFoundError(f"Parquet file not found: {PARQUET_FILE}")

    parquet = pq.ParquetFile(PARQUET_FILE)
    first_batch = next(parquet.iter_batches(batch_size=ROW_LIMIT), None)

    if first_batch is None:
        print(f"{PARQUET_FILE.name} is empty.")
        return

    first_rows = first_batch.to_pandas()
    print(f"First {len(first_rows)} rows of {PARQUET_FILE.name}:\n")
    print(first_rows.to_string(index=False))


if __name__ == "__main__":
    main()
