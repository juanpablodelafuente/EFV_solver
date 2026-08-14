from __future__ import annotations

"""Profile agreement measures calculated from preserved output data."""

from typing import Dict, Iterable, List, Mapping, Optional

import numpy as np
import pandas as pd

from .data_io import ReleaseDataError


def _uniform_spacing(depth: np.ndarray, benchmark: str, time_s: float) -> float:
    depth = np.asarray(depth, dtype=float)
    if depth.size < 2:
        return 1.0
    spacing = np.diff(depth)
    if np.any(spacing <= 0.0):
        raise ReleaseDataError(
            f"Depths must increase for {benchmark} at time {time_s:g} s."
        )
    if not np.allclose(spacing, spacing[0], rtol=1e-10, atol=1e-12):
        raise ReleaseDataError(
            f"Comparison depths must be uniformly spaced for {benchmark} "
            f"at time {time_s:g} s."
        )
    return float(spacing[0])


def field_metrics(test: np.ndarray,
                  reference: np.ndarray,
                  depth: np.ndarray,
                  benchmark: str,
                  time_s: float,
                  field: str,
                  units: str) -> dict:
    test = np.asarray(test, dtype=float)
    reference = np.asarray(reference, dtype=float)
    depth = np.asarray(depth, dtype=float)
    finite = np.isfinite(test) & np.isfinite(reference) & np.isfinite(depth)
    if finite.sum() < 2:
        raise ReleaseDataError(
            f"At least two common finite values are required for {benchmark}, "
            f"{field}, time {time_s:g} s."
        )

    test = test[finite]
    reference = reference[finite]
    depth = depth[finite]
    order = np.argsort(depth)
    test = test[order]
    reference = reference[order]
    depth = depth[order]
    dz = _uniform_spacing(depth, benchmark, time_s)

    difference = test - reference
    absolute = np.abs(difference)
    l2 = float(np.sqrt(np.sum(difference ** 2) * dz))
    reference_l2 = float(np.sqrt(np.sum(reference ** 2) * dz))
    maximum_index = int(np.argmax(absolute))
    nse_denominator = float(np.sum((reference - np.mean(reference)) ** 2))

    if np.std(test) > 0.0 and np.std(reference) > 0.0:
        correlation = float(np.corrcoef(test, reference)[0, 1])
    else:
        correlation = np.nan

    return {
        "benchmark": benchmark,
        "time_s": float(time_s),
        "field": field,
        "units": units,
        "number_of_comparison_depths": int(test.size),
        "relative_L2_percent": (
            np.nan if reference_l2 == 0.0 else 100.0 * l2 / reference_l2
        ),
        "maximum_absolute_error": float(absolute[maximum_index]),
        "maximum_error_depth_m": float(depth[maximum_index]),
        "mae": float(np.mean(absolute)),
        "rmse": float(np.sqrt(np.mean(difference ** 2))),
        "bias": float(np.mean(difference)),
        "pearson_r": correlation,
        "nse": (
            np.nan
            if nse_denominator == 0.0
            else float(1.0 - np.sum(difference ** 2) / nse_denominator)
        ),
    }


def calculate_profile_metrics(profiles: Dict[str, pd.DataFrame],
                              quantitative_benchmarks: Iterable[str],
                              comparison_times_s: Optional[Mapping[str, float]] = None) -> pd.DataFrame:
    rows: List[dict] = []
    comparison_times_s = comparison_times_s or {}
    for benchmark in quantitative_benchmarks:
        frame = profiles[benchmark]
        comparison_time = float(
            comparison_times_s.get(benchmark, frame["time_s"].max())
        )
        mask = np.isclose(
            frame["time_s"].to_numpy(dtype=float),
            comparison_time,
            rtol=0.0,
            atol=1e-7,
        )
        group = frame.loc[mask].sort_values("depth_m")
        if group.empty:
            raise ReleaseDataError(
                f"No agreement profile for {benchmark} at {comparison_time:g} s."
            )
        rows.append(field_metrics(
            group["theta_EFV"], group["theta_reference"], group["depth_m"],
            benchmark, comparison_time, "theta", "--",
        ))
        rows.append(field_metrics(
            group["psi_EFV_m"], group["psi_reference_m"], group["depth_m"],
            benchmark, comparison_time, "psi", "m",
        ))
    return pd.DataFrame(rows)


def agreement_table(metrics: pd.DataFrame,
                    benchmark_order: Iterable[str]) -> pd.DataFrame:
    rows = []
    for benchmark in benchmark_order:
        subset = metrics.loc[metrics["benchmark"] == benchmark]
        theta = subset.loc[subset["field"] == "theta"].iloc[0]
        psi = subset.loc[subset["field"] == "psi"].iloc[0]
        rows.append({
            "benchmark": benchmark,
            "comparison_time_s": theta["time_s"],
            "theta_relative_L2_percent": theta["relative_L2_percent"],
            "theta_maximum_absolute_error": theta["maximum_absolute_error"],
            "psi_relative_L2_percent": psi["relative_L2_percent"],
            "psi_maximum_absolute_error_m": psi["maximum_absolute_error"],
        })
    return pd.DataFrame(rows)
