from __future__ import annotations

"""Run the complete reproduction workflow."""

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from .data_io import (
    ReleaseDataError,
    build_hash_manifest,
    load_all_agreement_profiles,
    load_all_figure_data,
    load_reproduction_config,
    read_json,
    release_input_files,
    validate_required_tables,
)
from .metrics import agreement_table, calculate_profile_metrics
from .plots import plot_all_profiles
from .tables import copy_archived_performance_table, write_agreement_tables


def _compare_archived_agreement(reproduced: pd.DataFrame,
                                archived_path: Path) -> None:
    archived = pd.read_csv(archived_path)
    key_columns = [
        "benchmark",
        "theta_relative_L2_percent",
        "theta_maximum_absolute_error",
        "psi_relative_L2_percent",
        "psi_maximum_absolute_error_m",
    ]
    missing = [column for column in key_columns if column not in archived.columns]
    if missing:
        raise ReleaseDataError(
            f"Archived agreement table is missing columns: {missing}"
        )

    first = reproduced[key_columns].sort_values("benchmark").reset_index(drop=True)
    second = archived[key_columns].sort_values("benchmark").reset_index(drop=True)
    if list(first["benchmark"]) != list(second["benchmark"]):
        raise ReleaseDataError("Archived and reproduced agreement tables contain different benchmarks.")

    numeric = key_columns[1:]
    if not np.allclose(
        first[numeric].to_numpy(dtype=float),
        second[numeric].to_numpy(dtype=float),
        rtol=5e-10,
        atol=5e-12,
        equal_nan=True,
    ):
        raise ReleaseDataError(
            "Recalculated profile metrics do not match data/tables/profile_agreement.csv."
        )


def reproduce(root: Path,
              check_only: bool = False,
              output_directory: Path | None = None) -> Dict[str, Any]:
    root = root.resolve()
    config = load_reproduction_config(root)
    agreement_profiles = load_all_agreement_profiles(root, config)
    figure_data = load_all_figure_data(root, config)
    table_paths = validate_required_tables(root, config)

    provenance = root / "data" / "provenance.json"
    if not provenance.exists():
        raise ReleaseDataError(f"Missing provenance record: {provenance}")

    benchmark_config_path = root / "data" / "benchmark_configurations.json"
    if not benchmark_config_path.exists():
        raise ReleaseDataError(
            f"Missing benchmark configuration record: {benchmark_config_path}"
        )
    benchmark_configurations = read_json(benchmark_config_path).get("benchmarks", {})
    if set(benchmark_configurations) != set(config["paper_benchmarks"]):
        raise ReleaseDataError(
            "benchmark_configurations.json must contain all ten configured benchmarks."
        )

    metrics = calculate_profile_metrics(
        agreement_profiles,
        config["quantitative_benchmarks"],
        config.get("quantitative_comparison_times_s"),
    )
    agreement = agreement_table(metrics, config["quantitative_benchmarks"])
    _compare_archived_agreement(agreement, table_paths["profile_agreement"])

    result: Dict[str, Any] = {
        "paper_figures_validated": len(figure_data),
        "agreement_profiles_validated": len(agreement_profiles),
        "quantitative_benchmarks": len(config["quantitative_benchmarks"]),
        "check_only": bool(check_only),
    }
    if check_only:
        return result

    if output_directory is None:
        figure_directory = root / "figures"
        table_directory = root / "tables"
    else:
        output_directory = output_directory.resolve()
        figure_directory = output_directory / "figures"
        table_directory = output_directory / "tables"

    figures = plot_all_profiles(
        figure_data,
        config["paper_benchmarks"],
        figure_directory,
        figure_numbers=config.get("paper_figure_numbers"),
    )
    agreement_paths = write_agreement_tables(agreement, table_directory)
    performance_path = copy_archived_performance_table(
        table_paths["numerical_performance"], table_directory
    )

    def portable_path(path: Path) -> str:
        return (
            path.relative_to(root).as_posix()
            if path.is_relative_to(root)
            else str(path)
        )

    manifest = {
        "archive_version": config["archive_version"],
        "inputs": build_hash_manifest(root, release_input_files(root, config)),
        "generated_figures": [portable_path(path) for path in figures],
        "generated_tables": [
            portable_path(agreement_paths["csv"]),
            portable_path(agreement_paths["tex"]),
            portable_path(performance_path),
        ],
    }
    manifest_path = table_directory / "reproduction_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    result.update({
        "figures_created": len(figures),
        "agreement_csv": str(agreement_paths["csv"]),
        "agreement_tex": str(agreement_paths["tex"]),
        "performance_csv": str(performance_path),
        "manifest": str(manifest_path),
    })
    return result
