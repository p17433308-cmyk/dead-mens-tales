"""Tests for the examiner report and the enriched fingerprint."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from blackspot.models import DriveFacts, ReadSample, Verdict, TrimBehavior
from blackspot.fingerprint import classify
from blackspot.triage import triage
from blackspot.report import to_markdown


def test_report_contains_core_sections():
    beh, conf, why = classify([
        ReadSample(100, i + 1, "0" * 64, True, float(i)) for i in range(3)
    ])
    res = triage(DriveFacts(model="X", firmware_claims_zero=True,
                            idle_seconds_since_delete=60), beh, conf, why)
    md = to_markdown(res, case_id="CASE-9", examiner="Jane", exhibit="E1")
    for marker in ["# SSD Recoverability Triage Report", "CASE-9", "Jane",
                   "## 3. Finding", "LYING", "## 6. Limitations"]:
        assert marker in md, marker


def test_high_entropy_flagged_as_encrypted():
    reads = [ReadSample(100, i + 1, "a" * 64, False, float(i),
                        nonzero_fraction=1.0, shannon_entropy=7.9) for i in range(3)]
    beh, conf, why = classify(reads)
    assert beh is TrimBehavior.DRAT
    assert any("high entropy" in w for w in why), why


def test_partial_residual_flagged():
    reads = [ReadSample(100, i + 1, "b" * 64, False, float(i),
                        nonzero_fraction=0.5, shannon_entropy=5.0) for i in range(3)]
    beh, conf, why = classify(reads)
    assert any("partial residual" in w for w in why), why


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all report tests passed")
