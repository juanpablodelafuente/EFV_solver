import numpy as np

from src.metrics import field_metrics


def test_relative_l2_and_maximum_absolute_error():
    reference = np.array([1.0, 2.0, 3.0])
    test = np.array([1.0, 1.0, 4.0])
    depth = np.array([0.5, 1.5, 2.5])
    result = field_metrics(
        test, reference, depth, "Synthetic", 10.0, "theta", "--"
    )
    expected = 100.0 * np.sqrt(2.0) / np.sqrt(14.0)
    assert np.isclose(result["relative_L2_percent"], expected)
    assert np.isclose(result["maximum_absolute_error"], 1.0)
    assert result["number_of_comparison_depths"] == 3


def test_identical_profiles_have_zero_error():
    values = np.array([-3.0, -2.0, -1.0])
    result = field_metrics(
        values, values.copy(), np.array([0.1, 0.2, 0.3]),
        "Synthetic", 20.0, "psi", "m",
    )
    assert result["relative_L2_percent"] == 0.0
    assert result["maximum_absolute_error"] == 0.0
    assert result["rmse"] == 0.0
