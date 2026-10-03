"""Read-only, bounded-memory fingerprints and counts for the local Parquet files.

Run from the repository root. This script never writes to data/ or results/.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper" / "tables" / "source_data_descriptives.csv"
KEY = ["city_id", "store_id", "product_id"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def distinct(parquet: pq.ParquetFile) -> tuple[set[int], set[tuple[int, int, int]], set[str]]:
    """Stream the key and date columns in batches; never load the table at once."""
    products: set[int] = set()
    series: set[tuple[int, int, int]] = set()
    dates: set[str] = set()
    for batch in parquet.iter_batches(columns=KEY + ["dt"], batch_size=65_536):
        city, store, product, dt = (batch.column(i).to_pylist() for i in range(4))
        products.update(product)
        series.update(zip(city, store, product))
        dates.update(dt)
    return products, series, dates


def main() -> None:
    train = ROOT / "data" / "train.parquet"
    eval_file = ROOT / "data" / "eval.parquet"
    train_parquet = pq.ParquetFile(train)
    eval_parquet = pq.ParquetFile(eval_file)
    products, series, train_dates = distinct(train_parquet)
    _, eval_series, eval_dates = distinct(eval_parquet)

    rows = [
        ("train_rows", str(train_parquet.metadata.num_rows), "data/train.parquet", "Parquet metadata"),
        ("eval_rows", str(eval_parquet.metadata.num_rows), "data/eval.parquet", "Parquet metadata"),
        ("local_distinct_product_id", str(len(products)), "data/train.parquet", "streamed product_id batches"),
        ("train_distinct_series", str(len(series)), "data/train.parquet", "streamed (city_id, store_id, product_id) batches"),
        ("eval_distinct_series", str(len(eval_series)), "data/eval.parquet", "streamed (city_id, store_id, product_id) batches"),
        ("train_distinct_dates", str(len(train_dates)), "data/train.parquet", "streamed dt batches"),
        ("eval_distinct_dates", str(len(eval_dates)), "data/eval.parquet", "streamed dt batches"),
        ("train_sha256", sha256(train), "data/train.parquet", "streamed file bytes"),
        ("eval_sha256", sha256(eval_file), "data/eval.parquet", "streamed file bytes"),
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("metric", "value", "source_file", "method"))
        writer.writerows(rows)
    print(OUT)
    for metric, value, _, _ in rows:
        print(f"{metric}={value}")


if __name__ == "__main__":
    main()
