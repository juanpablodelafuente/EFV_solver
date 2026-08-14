# Data description

The `data` directory contains the numerical records underlying the benchmark
figures, profile-agreement measures and performance summaries. All depths are
measured vertically downward from the soil surface.

## Figure datasets

`figures/` contains one tidy CSV file for each manuscript figure from Figure 2
to Figure 11.

| Column | Description | Unit |
| --- | --- | --- |
| `benchmark` | Benchmark name | -- |
| `figure_number` | Manuscript figure number | -- |
| `field` | `psi` for pressure head or `theta` for water content | -- |
| `time_s` | Time associated with the series | s |
| `series` | `Initial`, `EFV` or `Reference` | -- |
| `depth_m` | Depth below the soil surface | m |
| `value` | Pressure head or volumetric water content | m or -- |
| `reference_source` | Method and benchmark-source record for the reference profile | -- |

Initial-condition rows use `time_s = 0`. EFV and reference rows use the final
comparison time specified in `../config/reproduction_config.json`. Figures
2--10 show pressure head and Figure 11 shows water content.

## Agreement profiles

`agreement/` contains one common-grid CSV file for each benchmark. These files
provide paired values at identical, uniformly spaced depths for the calculation
of the profile-agreement measures.

| Column | Description | Unit |
| --- | --- | --- |
| `benchmark` | Benchmark name | -- |
| `time_s` | Comparison time | s |
| `depth_m` | Common comparison depth | m |
| `theta_EFV` | EFV volumetric water content | -- |
| `theta_reference` | Reference volumetric water content | -- |
| `psi_EFV_m` | EFV pressure head | m |
| `psi_reference_m` | Reference pressure head | m |
| `reference_source` | Method and benchmark-source record for the reference profile | -- |

For a field value $q$ and reference value $q_r$, the reported relative
profile error is

$$
E_{L_2}=100\frac{\left[\sum_i(q_i-q_{r,i})^2\,\Delta z\right]^{1/2}}
{\left[\sum_i q_{r,i}^2\,\Delta z\right]^{1/2}}.
$$

The maximum absolute error is

$$
E_{\max}=\max_i\left|q_i-q_{r,i}\right|.
$$

## Archived tables

`tables/profile_agreement.csv` records the manuscript-ready relative
$L_2$ and maximum absolute errors for water content and pressure head. The
reproduction workflow recalculates every value from the common-grid profiles
and verifies agreement with this archived table.

`tables/numerical_performance.csv` records, for each benchmark, the grid size,
simulation duration, accepted time steps, final and limiting time-step values,
execution time, storage terms and mass-balance diagnostics.

## Benchmark configurations

`benchmark_configurations.json` records the grid, simulation duration,
hydraulic parameters, initial condition and boundary conditions used for each
benchmark. The entries retain the layer-specific parameters for the
heterogeneous Hills case.

## Provenance

`provenance.json` records the archive version, preparation date, dataset
composition and the publications used to define the benchmark configurations.
The SHA-256 manifest written by the reproduction workflow is available in
`../tables/reproduction_manifest.json`.

## Data licence

The numerical datasets are available under the Creative Commons Attribution
4.0 International License described in [`../LICENSE_DATA.md`](../LICENSE_DATA.md).
The publications identified in `reference_source` should be cited when their
benchmark configurations are reused.
