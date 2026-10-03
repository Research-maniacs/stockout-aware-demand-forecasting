# Saved Results

Metrics, manifests, and figures from the three runs reported in the paper.

```text
results/
|-- phase0_4/
|   |-- demo5000/   run S: Phases 0-4 on a stratified 5,000-series sample
|   `-- full50k/    run P: Phases 0-4 on all 50,000 series
`-- phase0_9_5k/
    |-- phase0_4/   run E: its own Phases 0-4 stage
    `-- phase5_9/   run E: Phases 5-9 metrics, manifests, and figures
```

- `phase0_4/full50k` covers Phases 0-4 only; the complete Phase 0-9 run (`phase0_9_5k`) uses 5,000 series.
- The TimesNet/TFT results in run E use a 600-series subset.
- `phase0_4/demo5000` and `phase0_9_5k/phase0_4` are separate executions; only the latter feeds run E's Phases 5-9.

Large intermediate files (feature tables, simulated histories, model checkpoints) are not included.
New runs are written to `results/runs/`, which is not tracked.
