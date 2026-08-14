from __future__ import annotations

"""Read and validate the archived benchmark data."""

import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


class ReleaseDataError(RuntimeError):
    """Raised when publication data are absent or inconsistent."""


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_reproduction_config(root: Path) -> dict:
    path = root / "config" / "reproduction_config.json"
    if not path.exists():
        raise ReleaseDataError(f"Missing reproduction configuration: {path}")
    return read_json(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_columns(frame: pd.DataFrame,
                     required: Iterable[str],
                     path: Path) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ReleaseDataError(f"{path} is missing columns: {missing}")


def load_agreement_profile(path: Path,
                           benchmark: str,
                           required_columns: Iterable[str],
                           comparison_time_s: float | None = None) -> pd.DataFrame:
    if not path.exists():
        raise ReleaseDataError(f"Missing agreement profile for {benchmark}: {path}")

    frame = pd.read_csv(path)
    _require_columns(frame, required_columns, path)
    if frame.empty:
        raise ReleaseDataError(f"Profile file is empty: {path}")

    names = set(frame["benchmark"].dropna().astype(str).str.strip())
    if names != {benchmark}:
        raise ReleaseDataError(
            f"{path} must contain only benchmark '{benchmark}', found {sorted(names)}."
        )

    numeric_columns = (
        "time_s", "depth_m", "theta_EFV", "theta_reference",
        "psi_EFV_m", "psi_reference_m",
    )
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if frame[["time_s", "depth_m"]].isna().any().any():
        raise ReleaseDataError(f"Non-numeric time or depth in {path}.")
    if not np.isfinite(frame[["time_s", "depth_m"]].to_numpy()).all():
        raise ReleaseDataError(f"Non-finite time or depth in {path}.")
    if (frame["time_s"] < 0.0).any() or (frame["depth_m"] < 0.0).any():
        raise ReleaseDataError(f"Negative time or depth in {path}.")

    if frame.duplicated(subset=["time_s", "depth_m"]).any():
        raise ReleaseDataError(f"Duplicate time/depth coordinates in {path}.")

    for time_s, group in frame.groupby("time_s", sort=True):
        depths = group["depth_m"].to_numpy(dtype=float)
        if depths.size > 1 and np.any(np.diff(np.sort(depths)) <= 0.0):
            raise ReleaseDataError(
                f"Depth coordinates are not unique at time {time_s:g} s in {path}."
            )

    efv_columns = ("theta_EFV", "psi_EFV_m")
    if frame[list(efv_columns)].isna().all(axis=0).any():
        raise ReleaseDataError(f"At least one EFV field is entirely absent in {path}.")

    has_reference = frame[["theta_reference", "psi_reference_m"]].notna().any(axis=1)
    if has_reference.any():
        sources = frame.loc[has_reference, "reference_source"].fillna("").astype(str).str.strip()
        if (sources == "").any():
            raise ReleaseDataError(
                f"Reference values in {path} require a non-empty reference_source."
            )

    if comparison_time_s is not None and not np.isclose(
        frame["time_s"].to_numpy(dtype=float), float(comparison_time_s),
        rtol=0.0, atol=1e-7,
    ).any():
        raise ReleaseDataError(
            f"No row in {path} matches the configured quantitative comparison "
            f"time {comparison_time_s:g} s."
        )

    return frame.sort_values(["time_s", "depth_m"]).reset_index(drop=True)


def load_all_agreement_profiles(root: Path,
                                config: dict) -> Dict[str, pd.DataFrame]:
    profiles: Dict[str, pd.DataFrame] = {}
    missing: List[str] = []

    comparison_times = config.get("quantitative_comparison_times_s", {})
    for benchmark in config["quantitative_benchmarks"]:
        filename = config["agreement_files"][benchmark]
        path = root / "data" / "agreement" / filename
        if not path.exists():
            missing.append(str(path.relative_to(root)))
            continue
        profiles[benchmark] = load_agreement_profile(
            path,
            benchmark,
            config["agreement_columns"],
            comparison_times.get(benchmark),
        )

    if missing:
        formatted = "\n  - ".join(missing)
        raise ReleaseDataError(
            "Final quantitative agreement profiles have not yet been inserted:\n  - "
            + formatted
        )
    return profiles


def load_figure_data(path: Path,
                     benchmark: str,
                     figure_number: int,
                     field: str,
                     required_times_s: Iterable[float],
                     required_columns: Iterable[str],
                     allowed_series: Iterable[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        raise ReleaseDataError(f"Missing Figure {figure_number} data: {path}")
    frame = pd.read_csv(path)
    _require_columns(frame, required_columns, path)
    if frame.empty:
        raise ReleaseDataError(f"Figure data file is empty: {path}")

    names = set(frame["benchmark"].dropna().astype(str).str.strip())
    if names != {benchmark}:
        raise ReleaseDataError(
            f"{path} must contain only benchmark '{benchmark}', found {sorted(names)}."
        )
    numbers = pd.to_numeric(frame["figure_number"], errors="coerce")
    if numbers.isna().any() or set(numbers.astype(int)) != {int(figure_number)}:
        raise ReleaseDataError(f"{path} must contain only Figure {figure_number} data.")
    fields = set(frame["field"].dropna().astype(str).str.strip().str.lower())
    if fields != {field}:
        raise ReleaseDataError(
            f"{path} must contain field '{field}', found {sorted(fields)}."
        )
    frame["field"] = field
    frame["series"] = frame["series"].astype(str).str.strip()
    allowed = set(allowed_series or ("EFV", "Reference"))
    if not set(frame["series"]).issubset(allowed):
        raise ReleaseDataError(
            f"{path} series values must be one of {sorted(allowed)}."
        )

    for column in ("time_s", "depth_m", "value"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame[["time_s", "depth_m", "value"]].isna().any().any():
        raise ReleaseDataError(f"Non-numeric figure value, time, or depth in {path}.")
    if not np.isfinite(frame[["time_s", "depth_m", "value"]].to_numpy()).all():
        raise ReleaseDataError(f"Non-finite figure value, time, or depth in {path}.")
    if (frame["time_s"] < 0.0).any() or (frame["depth_m"] < 0.0).any():
        raise ReleaseDataError(f"Negative time or depth in {path}.")
    if frame.duplicated(subset=["time_s", "series", "depth_m"]).any():
        raise ReleaseDataError(f"Duplicate time/series/depth rows in {path}.")

    comparison_rows = frame.loc[frame["series"].isin(("EFV", "Reference"))]
    actual_times = np.sort(comparison_rows["time_s"].unique())
    expected_times = np.sort(np.asarray(list(required_times_s), dtype=float))
    if actual_times.size != expected_times.size or not np.allclose(
        actual_times, expected_times, rtol=0.0, atol=1e-7
    ):
        raise ReleaseDataError(
            f"{path} times {actual_times.tolist()} do not match the manuscript "
            f"times {expected_times.tolist()}."
        )
    for time_s in expected_times:
        subset = comparison_rows.loc[
            np.isclose(comparison_rows["time_s"], time_s, rtol=0.0, atol=1e-7)
        ]
        if set(subset["series"]) != {"EFV", "Reference"}:
            raise ReleaseDataError(
                f"{path} requires both EFV and Reference at time {time_s:g} s."
            )
        for series in ("EFV", "Reference"):
            if (subset["series"] == series).sum() < 2:
                raise ReleaseDataError(
                    f"{path} needs at least two {series} values at {time_s:g} s."
                )

    initial = frame.loc[frame["series"] == "Initial"]
    if not initial.empty:
        if not np.allclose(
            initial["time_s"].to_numpy(dtype=float), 0.0, rtol=0.0, atol=1e-7
        ):
            raise ReleaseDataError(f"Initial rows in {path} must use time_s=0.")
        if len(initial) < 2:
            raise ReleaseDataError(f"{path} needs at least two Initial values.")

    references = frame.loc[frame["series"] == "Reference", "reference_source"]
    if (references.fillna("").astype(str).str.strip() == "").any():
        raise ReleaseDataError(f"Reference rows in {path} require reference_source.")
    return frame.sort_values(["time_s", "series", "depth_m"]).reset_index(drop=True)


def load_all_figure_data(root: Path,
                         config: dict) -> Dict[str, pd.DataFrame]:
    figures: Dict[str, pd.DataFrame] = {}
    missing: List[str] = []
    for benchmark in config["paper_benchmarks"]:
        path = root / "data" / "figures" / config["figure_files"][benchmark]
        if not path.exists():
            missing.append(str(path.relative_to(root)))
            continue
        figures[benchmark] = load_figure_data(
            path,
            benchmark,
            config["paper_figure_numbers"][benchmark],
            config["paper_plot_fields"][benchmark],
            config["paper_times_s"][benchmark],
            config["figure_columns"],
            allowed_series=config.get("figure_series"),
        )
    if missing:
        raise ReleaseDataError(
            "Final manuscript figure data have not yet been inserted:\n  - "
            + "\n  - ".join(missing)
        )
    return figures


def validate_required_tables(root: Path, config: dict | None = None) -> Dict[str, Path]:
    paths = {
        "profile_agreement": root / "data" / "tables" / "profile_agreement.csv",
        "numerical_performance": root / "data" / "tables" / "numerical_performance.csv",
    }
    missing = [str(path.relative_to(root)) for path in paths.values() if not path.exists()]
    if missing:
        raise ReleaseDataError(
            "Final publication tables have not yet been inserted:\n  - "
            + "\n  - ".join(missing)
        )

    if config is None:
        config = load_reproduction_config(root)

    agreement = pd.read_csv(paths["profile_agreement"])
    agreement_columns = {
        "benchmark", "comparison_time_s", "theta_relative_L2_percent",
        "theta_maximum_absolute_error", "psi_relative_L2_percent",
        "psi_maximum_absolute_error_m",
    }
    missing_agreement = sorted(agreement_columns.difference(agreement.columns))
    if missing_agreement:
        raise ReleaseDataError(
            "profile_agreement.csv is missing columns: "
            + ", ".join(missing_agreement)
        )
    if agreement["benchmark"].astype(str).tolist() != config["quantitative_benchmarks"]:
        raise ReleaseDataError(
            "profile_agreement.csv must contain all configured quantitative benchmarks "
            "once each and in the configured order."
        )

    performance = pd.read_csv(paths["numerical_performance"])
    if "benchmark" not in performance.columns:
        raise ReleaseDataError("numerical_performance.csv is missing benchmark.")
    expected_performance = config.get(
        "performance_benchmark_order", config["paper_benchmarks"]
    )
    if performance["benchmark"].astype(str).tolist() != expected_performance:
        raise ReleaseDataError(
            "numerical_performance.csv must contain all ten paper benchmarks "
            "once each and in the configured order."
        )
    return paths


def release_input_files(root: Path, config: dict) -> List[Path]:
    files = [
        root / "config" / "reproduction_config.json",
        root / "data" / "benchmark_configurations.json",
    ]
    files.extend(
        root / "data" / "agreement" / config["agreement_files"][benchmark]
        for benchmark in config["quantitative_benchmarks"]
    )
    files.extend(
        root / "data" / "figures" / config["figure_files"][benchmark]
        for benchmark in config["paper_benchmarks"]
    )
    files.extend([
        root / "data" / "tables" / "profile_agreement.csv",
        root / "data" / "tables" / "numerical_performance.csv",
        root / "data" / "provenance.json",
    ])
    return files


def build_hash_manifest(root: Path, files: Iterable[Path]) -> List[dict]:
    records = []
    for path in sorted(set(files)):
        if path.exists() and path.is_file():
            records.append({
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            })
    return records
