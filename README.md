# EFV benchmark figures and numerical results for the 1-D Richards equation

This repository accompanies the manuscript:

> *Explicit Mixed-Form Finite-Volume Solver for the 1-D Richards
> Equation: Stability Analysis and Benchmark Assessment*

It provides the numerical datasets used in the benchmark profile figures,
the common-grid profiles used to calculate agreement measures, the reported
performance summaries, and a Python workflow that validates the archived
values and recreates the figures and tables.

## Benchmarks

The archive covers ten benchmark cases. The plotted variable and comparison
time for each manuscript figure are listed below.

| Figure | Benchmark | Variable | Comparison time |
| ---: | --- | --- | ---: |
| 2 | Forsyth | Pressure head | 2400 h |
| 3 | Celia | Pressure head | 6 h |
| 4 | Warrick | Pressure head | 278 h |
| 5 | Warrick2 | Pressure head | 13 h |
| 6 | Zhi Li | Pressure head | 9 h |
| 7 | Zadeh | Pressure head | 5 h |
| 8 | Zeng | Pressure head | 1 h |
| 9 | Caviedes | Pressure head | 2 h |
| 10 | Miller | Pressure head | 54 h |
| 11 | Hills | Water content | 120 h |

Each profile figure contains the initial condition, the EFV result and the
implicit Picard reference result at the stated comparison time. Agreement
measures are evaluated on a common depth grid for both water content and
pressure head.

## Repository contents

| Path | Contents |
| --- | --- |
| `data/figures/` | Tidy numerical values plotted in Figures 2--11 |
| `data/agreement/` | Common-grid profiles used for the quantitative comparisons |
| `data/tables/` | Archived profile-agreement and performance summaries |
| `data/benchmark_configurations.json` | Grid, timing, hydraulic and boundary-condition settings |
| `data/provenance.json` | Dataset provenance and benchmark-source records |
| `figures/` | Ten publication-ready PNG profile figures |
| `tables/` | Recreated agreement and performance tables, including a LaTeX table |
| `src/` | Data validation, metric calculation, plotting and table-generation code |
| `tests/` | Numerical and end-to-end workflow tests |
| `config/reproduction_config.json` | File mappings, figure fields and comparison times |

Column definitions, units and the interpretation of each dataset are provided
in [`data/README.md`](data/README.md).

## Reproduce the figures and tables

Python 3.12 is recommended and is used by the automated workflow. Create a
virtual environment and install the required packages.

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the complete workflow in the repository:

```bash
python reproduce_all.py
```

This command validates the archived inputs, recalculates the profile-agreement
measures, recreates the ten figures, writes the result tables, and records the
input file hashes in `tables/reproduction_manifest.json`.

To keep the versioned outputs unchanged while making an independent copy, use:

```bash
python reproduce_all.py --output-dir reproduced_results
```

To validate all inputs and recalculate the agreement measures without writing
figures or tables, use:

```bash
python reproduce_all.py --check-only
```

## Tests

Install the development requirements and run the test suite:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

The automated workflow in `.github/workflows/reproduction-check.yml` runs the
same tests and reproduction check for each push and pull request.

## Licences

The analysis and plotting code is available under the MIT License; see
[`LICENSE`](LICENSE). Numerical data produced by the authors are available
under the Creative Commons Attribution 4.0 International License; see
[`LICENSE_DATA.md`](LICENSE_DATA.md). The publications used to define the
benchmark configurations are cited in the dataset records.

## Citation

Citation metadata are provided in [`CITATION.cff`](CITATION.cff). The archived
version DOI should be used to identify the exact dataset and code version used
in subsequent work.
