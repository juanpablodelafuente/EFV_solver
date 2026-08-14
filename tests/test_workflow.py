import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.metrics import agreement_table, calculate_profile_metrics
from src.workflow import reproduce


BENCHMARKS = [
    "Forsyth", "Celia", "Warrick", "Warrick2", "Zhi Li", "Zadeh",
    "Zeng", "Caviedes", "Miller", "Hills",
]
QUANTITATIVE = BENCHMARKS


def _profile(benchmark: str, offset: float) -> pd.DataFrame:
    depth = np.array([0.05, 0.15, 0.25])
    theta_reference = np.array([0.20, 0.25, 0.30]) + offset
    psi_reference = np.array([-3.0, -2.0, -1.0]) - offset
    return pd.DataFrame({
        "benchmark": benchmark,
        "time_s": 3600.0,
        "depth_m": depth,
        "theta_EFV": theta_reference + np.array([0.0, 0.001, -0.001]),
        "theta_reference": theta_reference,
        "psi_EFV_m": psi_reference + np.array([0.0, 0.01, -0.01]),
        "psi_reference_m": psi_reference,
        "reference_source": "Synthetic test fixture generated during pytest",
    })


def test_end_to_end_reproduction_uses_only_archived_csv(tmp_path: Path):
    root = tmp_path / "archive"
    (root / "config").mkdir(parents=True)
    (root / "data" / "agreement").mkdir(parents=True)
    (root / "data" / "figures").mkdir(parents=True)
    (root / "data" / "tables").mkdir(parents=True)
    agreement_files = {
        name: name.replace(" ", "_") + ".csv" for name in QUANTITATIVE
    }
    figure_files = {
        name: f"Figure_{index + 2:02d}_{name.replace(' ', '_')}.csv"
        for index, name in enumerate(BENCHMARKS)
    }
    config = {
        "archive_version": "test",
        "paper_benchmarks": BENCHMARKS,
        "quantitative_benchmarks": QUANTITATIVE,
        "agreement_files": agreement_files,
        "figure_files": figure_files,
        "paper_figure_numbers": {
            name: index + 2 for index, name in enumerate(BENCHMARKS)
        },
        "paper_plot_fields": {name: "psi" for name in BENCHMARKS},
        "paper_times_s": {name: [3600.0] for name in BENCHMARKS},
        "quantitative_comparison_times_s": {
            name: 3600.0 for name in QUANTITATIVE
        },
        "agreement_columns": [
            "benchmark", "time_s", "depth_m", "theta_EFV",
            "theta_reference", "psi_EFV_m", "psi_reference_m",
            "reference_source",
        ],
        "figure_columns": [
            "benchmark", "figure_number", "field", "time_s", "series",
            "depth_m", "value", "reference_source",
        ],
    }
    (root / "config" / "reproduction_config.json").write_text(
        json.dumps(config), encoding="utf-8"
    )

    profiles = {}
    for index, benchmark in enumerate(QUANTITATIVE):
        frame = _profile(benchmark, index * 0.001)
        profiles[benchmark] = frame
        frame.to_csv(
            root / "data" / "agreement" / agreement_files[benchmark], index=False
        )

    for index, benchmark in enumerate(BENCHMARKS):
        figure = pd.DataFrame({
            "benchmark": [benchmark] * 6,
            "figure_number": [index + 2] * 6,
            "field": ["psi"] * 6,
            "time_s": [3600.0] * 6,
            "series": ["EFV"] * 3 + ["Reference"] * 3,
            "depth_m": [0.05, 0.15, 0.25] * 2,
            "value": [-3.0, -2.0, -1.0, -3.0, -2.01, -0.99],
            "reference_source": [""] * 3 + ["Synthetic test fixture"] * 3,
        })
        figure.to_csv(
            root / "data" / "figures" / figure_files[benchmark], index=False
        )

    agreement = agreement_table(
        calculate_profile_metrics(profiles, QUANTITATIVE), QUANTITATIVE
    )
    agreement.to_csv(root / "data" / "tables" / "profile_agreement.csv", index=False)
    pd.DataFrame({"benchmark": BENCHMARKS, "accepted_steps": [10] * 10}).to_csv(
        root / "data" / "tables" / "numerical_performance.csv", index=False
    )
    (root / "data" / "provenance.json").write_text(
        json.dumps({"fixture": True}), encoding="utf-8"
    )
    (root / "data" / "benchmark_configurations.json").write_text(
        json.dumps({"benchmarks": {name: {"fixture": True} for name in BENCHMARKS}}),
        encoding="utf-8",
    )

    result = reproduce(root, check_only=False)
    assert result["paper_figures_validated"] == 10
    assert result["agreement_profiles_validated"] == 10
    assert result["quantitative_benchmarks"] == 10
    assert result["figures_created"] == 10
    assert len(list((root / "figures").glob("*.png"))) == 10
    assert (root / "tables" / "profile_agreement_reproduced.csv").is_file()
