from __future__ import annotations

"""Write reproducible CSV and LaTeX tables from archived values."""

from pathlib import Path
from typing import Dict

import pandas as pd


def _latex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def write_agreement_tables(table: pd.DataFrame, output_directory: Path) -> Dict[str, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    csv_path = output_directory / "profile_agreement_reproduced.csv"
    tex_path = output_directory / "profile_agreement_reproduced.tex"
    table.to_csv(csv_path, index=False)

    lines = [
        r"\begin{table}",
        r"\centering",
        r"\caption{Quantitative agreement between EFV and reference profiles.}",
        r"\label{tab:profile-agreement}",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Benchmark & $E_{2,\mathrm{rel}}(\theta)$ (\%) & $E_{\infty}(\theta)$ & $E_{2,\mathrm{rel}}(\psi)$ (\%) & $E_{\infty}(\psi)$ (m) \\",
        r"\midrule",
    ]
    for _, row in table.iterrows():
        lines.append(
            f"{_latex_escape(row['benchmark'])} & "
            f"{row['theta_relative_L2_percent']:.6g} & "
            f"{row['theta_maximum_absolute_error']:.6g} & "
            f"{row['psi_relative_L2_percent']:.6g} & "
            f"{row['psi_maximum_absolute_error_m']:.6g} \\\\"
        )
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ])
    tex_path.write_text("\n".join(lines), encoding="utf-8")
    return {"csv": csv_path, "tex": tex_path}


def copy_archived_performance_table(source: Path, output_directory: Path) -> Path:
    output_directory.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(source)
    path = output_directory / "numerical_performance_reproduced.csv"
    frame.to_csv(path, index=False)
    return path
