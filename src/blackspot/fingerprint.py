"""Controller-behavior fingerprinting.

Given repeated reads of the SAME trimmed LBA ranges, classify how the drive's
controller answers. This is the heart of "the drive is lying to you": a DZAT
drive returns zeros even while the physical NAND page still holds the data
(see ElcomSoft 2025 on DRAT/DZAT; Scanlon et al. on non-deterministic TRIM).

Input is a list of ReadSample captures (reproducible, offline). A real capture
harness (not shipped here for safety) issues TRIM then re-reads the same LBAs
multiple times with the device quiesced.
"""
from __future__ import annotations

from collections import defaultdict

from .models import ReadSample, TrimBehavior


def classify(samples: list[ReadSample]) -> tuple[TrimBehavior, float, list[str]]:
    """Return (behavior, confidence, rationale)."""
    rationale: list[str] = []
    if not samples:
        return TrimBehavior.UNKNOWN, 0.0, ["no read samples provided"]

    by_lba: dict[int, list[ReadSample]] = defaultdict(list)
    for s in samples:
        by_lba[s.lba].append(s)

    # Only LBAs read more than once tell us about determinism.
    repeated = {lba: rs for lba, rs in by_lba.items() if len(rs) >= 2}
    if not repeated:
        rationale.append("each LBA read only once; cannot judge determinism")
        # Still infer zero vs non-zero.
        all_zero = all(s.all_zero for s in samples)
        if all_zero:
            return TrimBehavior.DZAT, 0.4, rationale + ["all single reads zero"]
        return TrimBehavior.DRAT, 0.4, rationale + ["non-zero data present"]

    # Aggregate content statistics across all samples (richer than zero/non-zero).
    entropies = [s.shannon_entropy for s in samples if s.shannon_entropy]
    fractions = [s.nonzero_fraction for s in samples if s.nonzero_fraction]
    mean_entropy = sum(entropies) / len(entropies) if entropies else 0.0
    mean_nonzero = sum(fractions) / len(fractions) if fractions else 0.0

    def _content_notes() -> list[str]:
        notes: list[str] = []
        if mean_entropy >= 7.5:
            notes.append(
                f"residual data has high entropy ({mean_entropy:.2f} bits/byte) — "
                "likely encrypted or compressed; may indicate a SED container, so "
                "confirm key status before assuming recoverable plaintext"
            )
        elif entropies and mean_entropy > 0:
            notes.append(
                f"residual data entropy {mean_entropy:.2f} bits/byte — consistent "
                "with recoverable plaintext/structured data"
            )
        if fractions and 0.0 < mean_nonzero < 0.95:
            notes.append(
                f"partial residual: ~{mean_nonzero:.0%} of bytes non-zero — "
                "pages partially reclaimed; recover what remains promptly"
            )
        return notes

    non_deterministic_lbas = 0
    zero_lbas = 0
    nonzero_stable_lbas = 0
    for lba, rs in repeated.items():
        digests = {s.sha256 for s in rs}
        if len(digests) > 1:
            non_deterministic_lbas += 1
        elif all(s.all_zero for s in rs):
            zero_lbas += 1
        else:
            nonzero_stable_lbas += 1

    total = len(repeated)
    if non_deterministic_lbas / total >= 0.2:
        conf = 0.6 + 0.4 * (non_deterministic_lbas / total)
        rationale.append(
            f"{non_deterministic_lbas}/{total} LBAs returned different bytes "
            "across reads — controller is non-deterministic after TRIM"
        )
        rationale.extend(_content_notes())
        return TrimBehavior.NON_DETERMINISTIC, min(conf, 0.99), rationale

    if zero_lbas == total:
        rationale.append(
            f"all {total} repeated LBAs returned stable zeros — "
            "deterministic-zero-after-TRIM (DZAT); NAND may still hold data"
        )
        return TrimBehavior.DZAT, 0.85, rationale

    rationale.append(
        f"{nonzero_stable_lbas}/{total} LBAs returned stable non-zero data — "
        "deterministic-read-after-TRIM (DRAT); residual data readable host-side"
    )
    rationale.extend(_content_notes())
    return TrimBehavior.DRAT, 0.85, rationale
