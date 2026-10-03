# Verified Results Summary

## Phases 0-4: independent 5K versus 50K runs

| Result | 5K | 50K |
|---|---:|---:|
| Selected series | 5,000 | 50,000 |
| Selected series-days | 450,000 | 4,500,000 |
| Compute setting | `FAST_MODE=False` | `FAST_MODE=True` |
| Model-fit donor days | 163,250 | 1,630,675 |
| Tuning donor days | 45,097 | 450,872 |
| Calibration donor days | 42,773 | 426,447 |
| Donor share overall | 0.5580 | 0.5573 |
| Phase 4 median WAPE, A | 0.3334 | 0.3124 |
| Phase 4 median WAPE, B | 0.3361 | 0.3144 |
| Phase 4 median WAPE, C | 0.3358 | 0.3161 |
| Runtime | 1,194.9 s | 4,210.4 s |
| Peak RSS | 1.292 GB | 6.110 GB |
| Phase gates | All pass | All pass |

These are development/tuning results. The similar donor shares show that the deterministic 5K stratified sample broadly preserved this aggregate property. The WAPE difference is observed under different compute settings, so it should not be attributed solely to sample scale. Runtime is likewise not a clean scaling experiment.

These are two independent standalone executions. The 5K artifact in this table is not the Phase 0-4 predecessor used by the complete run.

## Complete Phases 0-9: 5K

The complete run evaluated 5,000 series. Its own Phase 0-4 handover used `FAST_MODE=False`, recorded q50 WAPEs of 0.333440, 0.336140, and 0.335759 for A/B/C, and took 1,483.8 seconds with peak RSS 1.280 GB. Those values happen to match the standalone 5K Phase 4 values, but the run timestamps, pandas version, hashes, and artifact lineage differ. The later Phase 5-9 half used `FAST_MODE=True`, derived `RUN_MODE=FAST`, and used a 600-series deep-model subset.

1. **Phases 0-4:** audited the data and temporal protocol, selected the 5K sample, produced the A/B/C histories, trained conventional baselines, and froze 12 LightGBM demand-quantile models.
2. **Prerequisite audit:** passed 10 checks, reproduced simulator masks and features, and checked 33 artifact hashes before proceeding.
3. **Phase 5:** task-aligned TimesNet recovery scored 290,397 hidden donor hours; 24 frozen TFT pipelines were evaluated. The official upstream reproduction remained partial.
4. **Phase 6:** the Kaplan-Meier implementation passed 8/8 unit tests and produced 207 support-counted pools.
5. **Phase 7:** pooled conformal calibration used 513,276 residuals, reported a 0.061 fallback share, and removed quantile crossings after monotone rearrangement.
6. **Phase 8:** nine ordering policies passed 10/10 hand tests, after which the final protocol lock was written.
7. **Phase 9:** the full-sample policies used 20,641 exact final donor candidate rows per 3x3 transfer cell. Kaplan-Meier sometimes scored fewer rows when its requested percentile was not estimable. The two TFT policies each scored 2,510 rows per cell from the 600-series subset; no fallback filled the other 4,400 series. The headline pooled-conformal policy's largest positive off-diagonal cost gap was +0.0472. Its advantage depends on the cost ratio: in the pre-specified paired contrast against the raw-sales LightGBM with residual quantiles (matched cells, 61,923 rows), the difference is +0.0208 [0.0016, 0.0432] when excess stock is more costly, -0.0091 [-0.0204, 0.0052] at equal costs, and -0.0790 [-0.0946, -0.0615] when shortage is more costly (`phase9_evaluation/bootstrap_paired_differences.csv`; negative favors pooled conformal).
8. **Real-history check:** the definite-miss lower-bound range was 0.0724-0.0895 over 105,000 final-week forecast records. A definite miss is an observed 16-hour sales total above the q90 forecast; because hidden demand can only add misses, this is a lower bound rather than real-demand coverage.

The run used 200 paired cluster-bootstrap repetitions across 866 `(city_id, store_id)` clusters. Reported bounds are 95% percentile intervals (2.5th and 97.5th bootstrap percentiles), with the same sampled cluster multiplicities applied to both sides of each difference. They are not BCa intervals, do not resample dates separately, and have no multiple-comparison adjustment. Phase 5-9 took 10,786 seconds and recorded a peak RSS of 5.064 GB.

The complete run's Phase 0-4 status retained one open item named `restart-and-run-all reproduces selected series, split IDs and simulator masks`. It was a first-execution check requiring an earlier fingerprint in the same output folder, not a model or data failure. The subsequent prerequisite audit independently reproduced masks/features and verified the 33 predecessor hashes.

Authoritative artifacts:

```text
results/phase0_4/demo5000/
results/phase0_4/full50k/
results/phase0_9_5k/phase5_9/manifests/final_summary.json
results/phase0_9_5k/phase5_9/metrics/phase_status_report.csv
```

The limitations of these results are discussed in Section VII of the paper ([paper/main.pdf](../paper/main.pdf)).
