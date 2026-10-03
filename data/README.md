# Data

This directory holds the FreshRetailNet-50K Version 1.0 Parquet files. They are not tracked by Git.

Download the dataset from the official source:

<https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K>

Expected layout:

```text
data/
|-- README.md
|-- train.parquet
`-- eval.parquet
```

Files used for the results in this repository:

| File | Rows | Series x dates | SHA-256 |
|---|---:|---|---|
| `train.parquet` | 4,500,000 | 50,000 x 90 | `6706832db892bbae4969c19d87e07975d2543d2ba7d7d4756360654785de5a3d` |
| `eval.parquet` | 350,000 | 50,000 x 7 | `1b118840664280c6b88bffc84c80ee1f54c05d911e354b7599e5da10995e960e` |

A series is identified by `(city_id, store_id, product_id)`. The hourly sales and stock-status fields contain
24 values per day; the forecast window used in this work is 06:00 to 21:59.

`train.parquet` contains 865 distinct `product_id` values, which matches the current dataset card. The dataset
technical report (arXiv:2505.16319v5) states 863 SKUs.

The upstream revision and download date of these files were not recorded, so the SHA-256 hashes above identify
the version used. The dataset card states a CC BY 4.0 license.
