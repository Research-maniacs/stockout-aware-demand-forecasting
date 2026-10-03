"""Generate the paper tables from the saved result files.

Run from the repository root:

    python paper/scripts/make_exhibits.py

The script reads results/ only and writes paper/tables/*.tex. No model is retrained.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABS = ROOT / "paper" / "tables"
DEMO = ROOT / "results/phase0_4/demo5000"
FULL = ROOT / "results/phase0_4/full50k"
MERGED = ROOT / "results/phase0_9_5k/phase0_4"
LATER = ROOT / "results/phase0_9_5k/phase5_9"
END = r" \\"
POLICY = "demand-quantile LightGBM + pooled conformal"
DISPLAY = {
    "seasonal_naive + residual quantile": "Seasonal naive + residual quantile",
    "raw-sales LightGBM + residual quantile": "Raw-sales LightGBM + residual quantile",
    "raw-sales quantile LightGBM": "Raw-sales quantile LightGBM",
    "demand-quantile LightGBM (uncalibrated)": "Demand-quantile LightGBM (uncalibrated)",
    "demand-quantile LightGBM + pooled conformal": "Demand-quantile LightGBM + pooled conformal",
    "Kaplan-Meier order percentile": "Kaplan--Meier order percentile",
    "demand-quantile + adaptive calibration (sensitivity)": "Demand-quantile + adaptive calibration (sensitivity)",
    "TFT (direct) + residual quantile": "TFT (direct) + residual quantile",
    "TimesNet->TFT + residual quantile": r"TimesNet$\rightarrow$TFT + residual quantile",
}
CONTRASTS = [
    ("pooled conformal vs uncalibrated", "Uncalibrated demand quantile", "Matched full sample"),
    ("demand-quantile (conformal) vs raw-sales point+residual", "Raw-sales LightGBM + residual", "Matched full sample"),
    ("demand-quantile (conformal) vs seasonal naive", "Seasonal naive + residual", "Matched full sample"),
    ("demand-quantile (conformal) vs Kaplan-Meier", "Kaplan--Meier percentile", "KM-supported rows"),
]


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def json_obj(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def one(rows: list[dict[str, str]], **filters: str) -> dict[str, str]:
    found = [row for row in rows if all(row[key] == value for key, value in filters.items())]
    if len(found) != 1:
        raise ValueError(f"Expected one row for {filters}; found {len(found)}")
    return found[0]


def count(value: str | int | float) -> str:
    return f"{int(float(value)):,}"


def signed(value: float, digits: int = 4) -> str:
    return f"{value:+.{digits}f}"


def math(text: str) -> str:
    """Wrap in math mode so LaTeX prints a true minus sign."""
    return f"${text}$"


def table(name: str, lines: list[str]) -> None:
    (TABS / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def split() -> None:
    rows = csv_rows(MERGED / "manifests/split_manifest.csv")
    names = {"model_fit": ("Model fit", "model fitting"), "tuning": ("Tuning", "model selection"),
             "calibration": ("Calibration", "calibration only"), "final_evaluation": ("Final", "locked evaluation")}
    lines = [r"\begin{tabularx}{\columnwidth}{@{}llc>{\raggedright\arraybackslash}X@{}}", r"\toprule",
             "Role & Days & Dates & Use" + END, r"\midrule"]
    for r in rows:
        role, use = names[r["use"]]
        days = f"{r['first_day']}--{r['last_day']}"
        dates = f"{r['first_date']} to {r['last_date']}"
        lines.append(f"{role} & {days} & {dates} & {use}" + END)
    lines += [r"\bottomrule", r"\end{tabularx}"]
    table("split.tex", lines)


def scale() -> None:
    roots = (DEMO, FULL)
    counts = {root: {r["quantity"]: r["value"] for r in csv_rows(root / "metrics/final_summary_counts.csv")} for root in roots}
    wape = {root: {r["mechanism"]: r["WAPE"] for r in csv_rows(root / "metrics/phase4_tuning_median_metrics.csv")} for root in roots}
    status = {root: json_obj(root / "run_status.json") for root in roots}
    fast = {root: json_obj(root / "manifests/provenance.json")["config"]["FAST_MODE"] for root in roots}
    assert (fast[DEMO], fast[FULL]) == (False, True), "Unexpected FAST_MODE settings in the standalone runs"
    rss = {root: csv_rows(root / "metrics/runtime_memory.csv") for root in roots}

    def row(label: str, cells: list[str]) -> str:
        return f"{label} & {cells[0]} & {cells[1]}" + END

    def count_row(label: str, quantity: str, fmt=count) -> str:
        return row(label, [fmt(counts[root][quantity]) for root in roots])

    lines = [r"\begin{tabular}{@{}lrr@{}}", r"\toprule", "Measure & Run S & Run P" + END, r"\midrule"]
    lines.append(row("Selected series", [count(status[r]["n_series"]) for r in roots]))
    lines.append(count_row("Selected series-days", "selected series-days"))
    lines.append(row("Hyperparameter search", ["reduced" if fast[r] else "full" for r in roots]))
    lines.append(count_row("Fit donor days", "donor days: model_fit (days 1-60)"))
    lines.append(count_row("Tuning donor days", "donor days: tuning (61-75)"))
    lines.append(count_row("Calibration donor days", "donor days: calibration (76-90, counted only)"))
    lines.append(count_row("Overall donor share", "donor share overall", lambda v: f"{float(v):.4f}"))
    lines.append(count_row("Training rows per mechanism", "Phase 4 train donor rows per mechanism (days 8-60)"))
    for mech in "ABC":
        lines.append(row(f"q50 tuning WAPE, {mech}", [f"{float(wape[r][mech]):.4f}" for r in roots]))
    lines.append(row("Runtime (s)", [f"{float(status[r]['total_seconds']):,.1f}" for r in roots]))
    lines.append(row("Peak memory (GB)", [f"{max(float(x['peak_rss_GB']) for x in rss[r]):.3f}" for r in roots]))
    lines += [r"\bottomrule", r"\end{tabular}"]
    table("standalone_scale.tex", lines)


def check_handover() -> None:
    """Section III states that run E's own Phase 0-4 stage reproduces run S exactly; check it."""
    w = {r["mechanism"]: r["WAPE"] for r in csv_rows(MERGED / "metrics/phase4_tuning_median_metrics.csv")}
    previous = {r["mechanism"]: r["WAPE"] for r in csv_rows(DEMO / "metrics/phase4_tuning_median_metrics.csv")}
    # Compare at full stored precision, not after rounding.
    assert w == previous, "The saved WAPEs are not exactly identical"
    assert json_obj(MERGED / "manifests/provenance.json")["config"]["FAST_MODE"] is False
    counts = [{r["quantity"]: r["value"] for r in csv_rows(root / "metrics/final_summary_counts.csv")} for root in (MERGED, DEMO)]
    assert counts[0] == counts[1], "Run E's donor counts differ from run S"
    fingerprints = [json_obj(root / "manifests/repro_fingerprints.json")[-1]["fingerprints"] for root in (MERGED, DEMO)]
    for key in ("selected_series_sha256", "split_manifest_sha256", "sim_mask_A_sha256", "sim_mask_B_sha256", "sim_mask_C_sha256"):
        assert fingerprints[0][key] == fingerprints[1][key], f"{key} differs between runs E and S"


def policy_panels(lock: dict, orders: list[dict[str, str]]) -> None:
    betas = [str(s["beta"]) for s in lock["cost_scenarios"]]
    header = " & ".join(rf"$\beta={float(s['beta']):.2f}$" for s in lock["cost_scenarios"])
    lines = [r"\begin{tabular}{@{}llrrrr@{}}", r"\toprule",
             r" & & & \multicolumn{3}{c}{Mean cost}" + END, r"\cmidrule(l){4-6}",
             "Policy & Population & $n$ & " + header + END]
    panels = (("full sample", "Full sample", 7, r"(a) Full-sample exact-donor candidates"),
              ("deep subsample", "Deep subset", 2,
               rf"(b) Declared deep subset of {lock['deep_subsample']} series (separate population)"))
    for population, label, expected, heading in panels:
        rows = {}
        for r in orders:
            if r["population"] == population and r["train_mech"] == "A" and r["test_hist"] == "A":
                rows.setdefault(r["policy"], {})[r["beta"]] = r
        assert len(rows) == expected, f"{population}: expected {expected} policies"
        best = {b: min(float(rows[p][b]["mean cost"]) for p in rows) for b in betas}
        lines += [r"\midrule", rf"\multicolumn{{6}}{{@{{}}l}}{{\emph{{{heading}}}}}" + END]
        for policy in sorted(rows, key=lock["policies"].index):
            ns = {rows[policy][b]["n"] for b in betas}
            assert len(ns) == 1, f"{policy}: n differs across cost settings in the A/A cell"
            cells = []
            for b in betas:
                cost = float(rows[policy][b]["mean cost"])
                text = f"{cost:.4f}"
                cells.append(rf"\textbf{{{text}}}" if cost == best[b] else text)
            lines.append(f"{DISPLAY[policy]} & {label} & {count(ns.pop())} & " + " & ".join(cells) + END)
    lines += [r"\bottomrule", r"\end{tabular}"]
    table("policy_panels.tex", lines)


def cost_scenarios(lock: dict, orders: list[dict[str, str]]) -> None:
    lines = [r"\begin{tabular}{@{}llrrrr@{}}", r"\toprule",
             r"History & Population & $n$ & Mean cost & Fill rate & Leftover" + END]
    for scenario in lock["cost_scenarios"]:
        heading = f"{scenario['scenario'].capitalize()} ($\\beta={float(scenario['beta']):.2f}$)"
        lines += [r"\midrule", rf"\multicolumn{{6}}{{@{{}}l}}{{\emph{{{heading}}}}}" + END]
        for mech in "ABC":
            r = one(orders, scenario=scenario["scenario"], beta=str(scenario["beta"]),
                    policy=POLICY, train_mech=mech, test_hist=mech)
            lines.append(f"{mech} & Full sample & {count(r['n'])} & {float(r['mean cost']):.4f} "
                         f"& {float(r['fill rate']):.3f} & {float(r['leftover share']):.3f}" + END)
    lines += [r"\bottomrule", r"\end{tabular}"]
    table("cost_scenarios.tex", lines)


def paired_contrasts(lock: dict, boot: list[dict[str, str]]) -> None:
    lines = [r"\begin{tabular}{@{}lllrrr@{}}", r"\toprule",
             r"Pooled conformal minus & Cost setting & Population & $n$ & Difference & 95\% percentile interval" + END,
             r"\midrule"]
    for index, (key, label, population) in enumerate(CONTRASTS):
        if index:
            lines.append(r"\addlinespace")
        for scenario in lock["cost_scenarios"]:
            r = one(boot, scenario=scenario["scenario"], beta=str(scenario["beta"]),
                    comparison=f"{key} (mean cost difference)")
            interval = f"[{float(r['lo']):.4f}, {float(r['hi']):.4f}]"
            lines.append(f"{label} & {scenario['scenario'].capitalize()} & {population} & {count(r['n'])} "
                         f"& {math(signed(float(r['point'])))} & {math(interval)}" + END)
    lines += [r"\bottomrule", r"\end{tabular}"]
    table("paired_contrasts.tex", lines)


def transfer(orders: list[dict[str, str]], boot: list[dict[str, str]]) -> None:
    gaps = [r for r in csv_rows(LATER / "phase9_evaluation/transfer_gaps_cost.csv")
            if r["beta"] == "0.75" and r["policy"] == POLICY]
    assert len(gaps) == 6
    gaps.sort(key=lambda r: (r["train_mech"], r["test_hist"]))
    lines = [r"\begin{tabular}{@{}cclrrrrr@{}}", r"\toprule",
             r"Train & Test history & Population & $n$ & Matched & Unseen & Gap & 95\% percentile interval" + END,
             r"\midrule"]
    for r in gaps:
        a, b = r["train_mech"], r["test_hist"]
        order = one(orders, beta="0.75", policy=POLICY, train_mech=a, test_hist=b)
        ci = one(boot, beta="0.75", comparison=f"transfer gap {a}->{b} (unseen minus matched mean cost)")
        gap = float(r["cost transfer gap"])
        assert abs(gap - float(ci["point"])) < 1e-9, f"Gap mismatch for {a}->{b}"
        assert int(float(ci["n"])) == int(float(order["n"])), f"Bootstrap n differs from scored n for {a}->{b}"
        interval = f"[{float(ci['lo']):.4f}, {float(ci['hi']):.4f}]"
        lines.append(f"{a} & {b} & Full sample & {count(order['n'])} & {float(r['matched mean cost']):.4f} "
                     f"& {float(r['unseen mean cost']):.4f} & {math(signed(gap))} & {math(interval)}" + END)
    lines += [r"\bottomrule", r"\end{tabular}"]
    table("transfer.tex", lines)


def real_history() -> None:
    summary = csv_rows(LATER / "phase9_evaluation/real_history_miss_summary.csv")
    intervals = csv_rows(LATER / "phase9_evaluation/real_history_miss_bootstrap.csv")
    lines = [r"\begin{tabular}{@{}llrrr@{}}", r"\toprule",
             r"Trained on & Population & Rows & Bound & 95\% interval" + END, r"\midrule"]
    for r in summary:
        m = r["train_mech"]
        ci = one(intervals, train_mech=m)
        interval = f"[{float(ci['lo']):.4f}, {float(ci['hi']):.4f}]"
        lines.append(f"{m} & Real history & {count(r['rows'])} & {float(r['definite-miss lower bound']):.4f} "
                     f"& {math(interval)}" + END)
    lines += [r"\bottomrule", r"\end{tabular}", "", r"\vspace{6pt}", ""]

    severity = csv_rows(LATER / "phase9_evaluation/real_history_miss_by_severity.csv")
    labels = {"0 h (complete)": "0 (complete day)", "1-4 h": "1--4", "5-8 h": "5--8", "9-16 h": "9--16"}
    lines += [r"\begin{tabular}{@{}lrrrr@{}}", r"\toprule",
              r"Recorded stockout hours & Rows & A & B & C" + END, r"\midrule"]
    total = 0
    for key, stratum in labels.items():
        cells = [one(severity, train_mech=m, severity=key) for m in "ABC"]
        sizes = {c["size"] for c in cells}
        assert len(sizes) == 1, f"Stratum size differs by training history for {key}"
        size = sizes.pop()
        total += int(size)
        values = " & ".join(f"{float(c['mean']):.4f}" for c in cells)
        lines.append(f"{stratum} & {count(size)} & {values}" + END)
    assert total == int(float(summary[0]["rows"])), "Severity strata do not sum to the real-history rows"
    lines += [r"\bottomrule", r"\end{tabular}"]
    table("real_miss.tex", lines)


def ablations() -> None:
    evidence = csv_rows(LATER / "metrics/ablation_table.csv")
    # (ablation number, label, values quoted from the result text, scope)
    specifications = [
        ("1.", "Raw-sales vs demand-quantile", ("0.4075", "0.3984"), "Equal-cost matched cells"),
        ("2.", "Uncalibrated vs pooled q90 coverage", ("0.8121", "0.8832"), "Final donor proxy; nominal 0.90"),
        ("5.", "Direct vs recovered-history TFT", ("0.4999", "0.4690"), "Equal-cost deep subset"),
        ("7.", "Short versus full lag set", (), "Not run after the lock"),
        ("8.", "Static vs adaptive calibration", ("0.3984", "0.4039"), "Equal-cost sensitivity"),
        ("9.", "One-day vs two-day inventory", ("0.3984", "0.2579"), "Hypothetical carry-over"),
        ("10.", "Contract vs oracle-weather WAPE", ("33.48%", "33.40%"), "Target-day oracle; not deployable"),
    ]
    lines = [r"\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}Xl>{\raggedright\arraybackslash}p{0.34\linewidth}@{}}",
             r"\toprule", "Recorded diagnostic & Values & Scope" + END, r"\midrule"]
    for prefix, title, values, scope in specifications:
        record = next((r for r in evidence if r["ablation"].startswith(prefix)), None)
        expected = values or ("NOT AVAILABLE",)
        if record is None or any(value not in record["result"] for value in expected):
            raise ValueError(f"Ablation {prefix} does not match results/.../ablation_table.csv")
        cell = " / ".join(v.replace("%", r"\%") for v in values) if values else "Not available"
        lines.append(f"{title} & {cell} & {scope}" + END)
    lines += [r"\bottomrule", r"\end{tabularx}"]
    table("ablations.tex", lines)


def main() -> None:
    TABS.mkdir(parents=True, exist_ok=True)
    lock = json_obj(LATER / "manifests/final_test_lock.json")
    orders = csv_rows(LATER / "phase9_evaluation/final_order_metrics.csv")
    boot = csv_rows(LATER / "phase9_evaluation/bootstrap_paired_differences.csv")
    assert set(lock["policies"]) == {r["policy"] for r in orders}
    assert {(r["scenario"], float(r["beta"])) for r in orders} == {
        (r["scenario"], float(r["beta"])) for r in lock["cost_scenarios"]}
    assert lock["n_series"] == 5000 and lock["deep_subsample"] == 600
    split()
    scale()
    check_handover()
    policy_panels(lock, orders)
    cost_scenarios(lock, orders)
    paired_contrasts(lock, boot)
    transfer(orders, boot)
    real_history()
    ablations()
    print(f"Wrote tables to {TABS}")


if __name__ == "__main__":
    main()
