import hashlib
import json
from pathlib import Path

from src.data_io import load_reproduction_config
from src.workflow import reproduce


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def test_archived_data_passes_complete_validation():
    result = reproduce(ROOT, check_only=True)
    assert result == {
        "paper_figures_validated": 10,
        "agreement_profiles_validated": 10,
        "quantitative_benchmarks": 10,
        "check_only": True,
    }


def test_versioned_figure_set_is_complete():
    config = load_reproduction_config(ROOT)
    figure_paths = sorted((ROOT / "figures").glob("*.png"))
    assert len(figure_paths) == len(config["paper_benchmarks"]) == 10
    for path in figure_paths:
        assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_reproduction_manifest_matches_archived_inputs():
    manifest = json.loads(
        (ROOT / "tables" / "reproduction_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["archive_version"] == "1.0.0"
    assert len(manifest["inputs"]) == 25
    for record in manifest["inputs"]:
        path = ROOT / record["path"]
        assert path.is_file()
        assert path.stat().st_size == record["size_bytes"]
        assert _sha256(path) == record["sha256"]
