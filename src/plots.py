from __future__ import annotations

"""Create the benchmark profile visualisations."""

import re
from pathlib import Path
from typing import Dict, List, Mapping, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("_")


def _time_label(time_s: float) -> str:
    if time_s >= 360.0:
        return f"{time_s / 3600.0:g} h"
    if time_s >= 60.0:
        return f"{time_s / 60.0:g} min"
    return f"{time_s:g} s"


def plot_benchmark_profiles(benchmark: str,
                            frame: pd.DataFrame,
                            output_directory: Path,
                            figure_number: Optional[int] = None) -> Path:
    output_directory.mkdir(parents=True, exist_ok=True)
    comparison_times = sorted(
        frame.loc[frame["series"].isin(("EFV", "Reference")), "time_s"].unique()
    )
    field = str(frame["field"].iloc[0]).lower()

    fig, axis = plt.subplots(figsize=(7.2, 7.2))
    plotted = False

    initial = frame.loc[frame["series"] == "Initial"].sort_values("depth_m")
    if not initial.empty:
        axis.plot(
            initial["value"], initial["depth_m"], color="0.55",
            linestyle=":", linewidth=1.7, label="Initial",
        )

    for time_s in comparison_times:
        group = frame.loc[frame["time_s"] == time_s].sort_values("depth_m")
        label = _time_label(float(time_s))
        efv = group.loc[group["series"] == "EFV"].sort_values("depth_m")
        reference = group.loc[group["series"] == "Reference"].sort_values("depth_m")
        one_time = len(comparison_times) == 1
        axis.plot(
            efv["value"], efv["depth_m"], color="#1f77b4",
            linewidth=2.0, label="EFV" if one_time else f"EFV t={label}",
        )
        axis.plot(
            reference["value"], reference["depth_m"], color="#ff7f0e",
            linestyle="--", linewidth=2.0,
            label="Implicit Picard" if one_time else f"Implicit Picard t={label}",
        )
        plotted = True

    title_field = "water content" if field == "theta" else "pressure head"
    title = f"{benchmark}: {title_field}"
    if comparison_times:
        metric_time = comparison_times[-1]
        metric_group = frame.loc[
            np.isclose(frame["time_s"], metric_time, rtol=0.0, atol=1e-7)
            & frame["series"].isin(("EFV", "Reference"))
        ]
        efv_metric = metric_group.loc[
            metric_group["series"] == "EFV", ["depth_m", "value"]
        ].rename(columns={"value": "efv"})
        reference_metric = metric_group.loc[
            metric_group["series"] == "Reference", ["depth_m", "value"]
        ].rename(columns={"value": "reference"})
        paired = efv_metric.merge(reference_metric, on="depth_m", how="inner")
        if len(paired) >= 2:
            difference = paired["efv"].to_numpy() - paired["reference"].to_numpy()
            denominator = np.linalg.norm(paired["reference"].to_numpy())
            relative_l2 = np.nan if denominator == 0.0 else 100.0 * np.linalg.norm(difference) / denominator
            maximum = float(np.max(np.abs(difference)))
            unit = " m" if field == "psi" else ""
            title += (
                "\n"
                + rf"relative $L_2$={relative_l2:.5g}%, $E_\infty$={maximum:.4g}{unit}"
            )

    if field == "theta":
        axis.set_xlabel(r"Water content, $\theta$ [-]")
    else:
        axis.set_xlabel(r"Pressure head, $\psi$ [m]")
    axis.set_title(title)
    axis.set_ylabel(r"Depth, $z$ [m]")
    axis.grid(True, alpha=0.35)
    axis.invert_yaxis()
    if plotted:
        axis.legend(fontsize=8)
    else:
        axis.text(
            0.5, 0.5, "No profile data reported",
            ha="center", va="center", transform=axis.transAxes,
        )

    fig.tight_layout()
    prefix = f"Figure_{figure_number:02d}_" if figure_number is not None else ""
    path = output_directory / f"{prefix}{safe_name(benchmark)}_{field}_profiles.png"
    temporary_path = path.with_suffix(".png.tmp")
    png_signature = b"\x89PNG\r\n\x1a\n"
    try:
        temporary_path.unlink(missing_ok=True)
        fig.savefig(
            temporary_path, format="png", dpi=300, bbox_inches="tight"
        )
        if temporary_path.stat().st_size <= len(png_signature):
            raise OSError(f"Matplotlib produced an empty figure: {path.name}")
        with temporary_path.open("rb") as handle:
            if handle.read(len(png_signature)) != png_signature:
                raise OSError(f"Matplotlib produced an invalid PNG: {path.name}")
        temporary_path.replace(path)
    finally:
        plt.close(fig)
        temporary_path.unlink(missing_ok=True)
    return path


def plot_all_profiles(profiles: Dict[str, pd.DataFrame],
                      benchmark_order: List[str],
                      output_directory: Path,
                      figure_numbers: Optional[Mapping[str, int]] = None) -> List[Path]:
    figure_numbers = figure_numbers or {}
    return [
        plot_benchmark_profiles(
            benchmark,
            profiles[benchmark],
            output_directory,
            figure_number=figure_numbers.get(benchmark),
        )
        for benchmark in benchmark_order
    ]
