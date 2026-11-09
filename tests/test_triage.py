"""Smoke tests for the BLACKSPOT triage engine."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from blackspot.models import DriveFacts, ReadSample, Verdict, TrimBehavior
from blackspot.fingerprint import classify
from blackspot.triage import triage


def _reads(sha, zero, n=3, lba=100):
    return [ReadSample(lba=lba, attempt=i + 1, sha256=sha, all_zero=zero, timestamp=float(i))
            for i in range(n)]


def test_dzat_is_lying():
    beh, conf, why = classify(_reads("0" * 64, True))
    assert beh is TrimBehavior.DZAT
    res = triage(DriveFacts(firmware_claims_zero=True, idle_seconds_since_delete=60),
                 beh, conf, why)
    assert res.verdict is Verdict.LYING


def test_drat_is_alive():
    beh, conf, why = classify(_reads("a" * 64, False))
    assert beh is TrimBehavior.DRAT
    res = triage(DriveFacts(), beh, conf, why)
    assert res.verdict is Verdict.ALIVE


def test_crypto_erase_short_circuits():
    beh, conf, why = classify(_reads("0" * 64, True))
    res = triage(DriveFacts(is_sed=True, crypto_erase_confirmed=True), beh, conf, why)
    assert res.verdict is Verdict.CRYPTO_ERASED


def test_non_deterministic_detected():
    samples = [
        ReadSample(100, 1, "a" * 64, False, 0.0),
        ReadSample(100, 2, "b" * 64, False, 1.0),
        ReadSample(100, 3, "c" * 64, False, 2.0),
    ]
    beh, conf, why = classify(samples)
    assert beh is TrimBehavior.NON_DETERMINISTIC


def test_fading_after_long_idle():
    beh, conf, why = classify(_reads("0" * 64, True))
    res = triage(DriveFacts(firmware_claims_zero=True, idle_seconds_since_delete=7200),
                 beh, conf, why)
    assert res.verdict is Verdict.FADING


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
