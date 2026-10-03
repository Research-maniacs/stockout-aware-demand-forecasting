# Stockout-Aware Demand Forecasting and Newsvendor Ordering on FreshRetailNet-50K

This repository contains the code, saved results, and LaTeX sources for the paper
*Stockout-Aware Demand Forecasting and Newsvendor Ordering on FreshRetailNet-50K*.
The compiled paper is [paper/main.pdf](paper/main.pdf).

Recorded sales understate demand whenever a product sells out. We study demand forecasting and
newsvendor ordering on [FreshRetailNet-50K](https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K),
a fresh-retail panel with hourly stockout flags. Days without a flagged stockout between 06:00 and 21:59
("donor days") give an exact, though selected, demand proxy. Three simulated stockout mechanisms (A, B, C)
censor these days in different ways, so a model trained on one censored history can be scored on another
against the same outcomes. The pipeline compares LightGBM, TimesNet, TFT, and Kaplan-Meier baselines,
conformal calibration, and nine ordering policies under a protocol locked before the final week was scored.

## Repository structure

```text
.
|-- notebooks/
|   |-- FreshRetailNet_Phases_0_to_4.ipynb                  Phases 0-4 (data, simulation, baselines, LightGBM)
|   |-- FreshRetailNet_Phases_0_to_4_FULL50K_executed.ipynb executed 50K run of Phases 0-4
|   `-- FreshRetailNet_Phases_0_to_9.ipynb                  complete pipeline, Phases 0-9
|-- data/                    dataset location (Parquet files are not tracked)
|-- results/
|   |-- phase0_4/demo5000/   run S: Phases 0-4 on a stratified 5,000-series sample
|   |-- phase0_4/full50k/    run P: Phases 0-4 on all 50,000 series
|   `-- phase0_9_5k/         run E: complete Phases 0-9 on 5,000 series
|-- paper/
|   |-- main.tex, main.pdf   manuscript (IEEE conference format)
|   |-- sections/            section sources
|   |-- tables/, figures/    tables and figures generated from results/
|   |-- references.bib
|   `-- scripts/             scripts that regenerate the tables and figures
|-- scripts/                 small data utilities
`-- docs/results.md          summary of the main results
```

## Getting started

```bash
git clone https://github.com/Research-maniacs/stockout-aware-demand-forecasting.git
cd stockout-aware-demand-forecasting
```

## Data

The dataset is not included in this repository. Download Version 1.0 of
[Dingdong-Inc/FreshRetailNet-50K](https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K)
and place the files at `data/train.parquet` and `data/eval.parquet`. The results in this repository
were produced with the files below; see [data/README.md](data/README.md) for the schema.

| File | Rows | SHA-256 |
|---|---:|---|
| `train.parquet` | 4,500,000 | `6706832db892bbae4969c19d87e07975d2543d2ba7d7d4756360654785de5a3d` |
| `eval.parquet` | 350,000 | `1b118840664280c6b88bffc84c80ee1f54c05d911e354b7599e5da10995e960e` |

## Running the experiments

The experiments were run with Python 3.11.15 on Linux. The package versions of each run are recorded in
its `manifests/provenance.json` under `results/`.

The notebooks read their input and output locations from environment variables. For example, to run
Phases 0-4 on a 5,000-series sample (PowerShell):

```powershell
$env:FRN_DATA_DIR = (Resolve-Path .\data).Path
$env:FRN_OUTPUT_DIR = (Join-Path (Get-Location) 'results\runs\phase0_4_demo')
$env:FRN_FULL_RUN = '0'
$env:FRN_SAMPLE_N = '5000'
jupyter lab
```

Then open [notebooks/FreshRetailNet_Phases_0_to_4.ipynb](notebooks/FreshRetailNet_Phases_0_to_4.ipynb)
or, for the complete pipeline, [notebooks/FreshRetailNet_Phases_0_to_9.ipynb](notebooks/FreshRetailNet_Phases_0_to_9.ipynb).
New runs are written under `results/runs/`, which is not tracked. The saved runs took between about
20 minutes and several hours and used up to 6.1 GB of memory.

## Reproducing the paper

The tables and figures are generated from the saved files in `results/`; no model is retrained.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r paper\scripts\requirements.txt

.\.venv\Scripts\python paper\scripts\make_exhibits.py         # tables and transfer-gap figure
.\.venv\Scripts\python paper\scripts\make_diagrams.py         # schematic figures
.\.venv\Scripts\python paper\scripts\stream_descriptives.py   # dataset counts and hashes (needs data/)
```

Build the PDF with [Tectonic](https://tectonic-typesetting.github.io/) or any TeX Live installation:

```powershell
cd paper
tectonic main.tex        # or: latexmk -pdf main.tex
```

## Main results

| | Run S (5K) | Run P (50K) |
|---|---:|---:|
| Donor share | 0.5580 | 0.5573 |
| q50 tuning WAPE, mechanism A | 0.3334 | 0.3124 |
| Runtime | 1,194.9 s | 4,210.4 s |

On the locked final week of run E, no ordering policy wins under every cost ratio. When shortage costs three
times as much as a leftover unit, LightGBM demand quantiles with pooled conformal calibration give the lowest
mean cost among the full-sample policies; when leftovers cost more, a raw-sales LightGBM with residual
quantiles is cheaper. Evaluating the calibrated policy on a history it was not trained on raises its mean cost
by at most 0.0472 normalized units. See [docs/results.md](docs/results.md) and the paper for details.

## Limitations

- Observed sales are not uncensored demand; donor days are a selected demand proxy, so final-week scoring
  uses donor rows only, and real censored histories get only a lower bound on q90 misses.
- The complete Phase 0-9 run covers 5,000 series, and the TimesNet/TFT experiments use a 600-series subset.
  The 50,000-series run covers Phases 0-4 only.
- The official baseline was reproduced only in part.
- Runs S and P used different tuning settings, so their runtime and WAPE differences are not pure scale effects.

## License

The FreshRetailNet-50K dataset is distributed by Dingdong-Inc under CC BY 4.0 and is not redistributed here.
