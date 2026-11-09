"""Core data models for BLACKSPOT triage."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
import json


class TrimBehavior(str, Enum):
    """How a controller answers reads to a TRIMmed LBA range."""

    DZAT = "deterministic_zero_after_trim"      # always returns zeros
    DRAT = "deterministic_read_after_trim"      # always returns the SAME bytes
    NON_DETERMINISTIC = "non_deterministic"     # reads differ between attempts
    NO_TRIM = "trim_not_issued_or_unsupported"  # TRIM never reached the device
    UNKNOWN = "unknown"


class Verdict(str, Enum):
    """The black spot itself — the triage conclusion."""

    ALIVE = "alive"          # evidence very likely still in NAND, pursue recovery
    LYING = "lying"          # drive returns zeros but NAND likely still holds data
    FADING = "fading"        # within a shrinking pre-GC window, act fast
    SCUTTLED = "scuttled"    # GC/crypto-erase has almost certainly destroyed it
    CRYPTO_ERASED = "crypto_erased"  # SED crypto-erase: key gone, game over


@dataclass
class DriveFacts:
    """Field-observable facts about the drive under triage."""

    model: str = "unknown"
    controller_family: str = "unknown"
    is_sed: bool = False                 # self-encrypting drive
    crypto_erase_confirmed: bool = False
    trim_enabled: bool = True
    powered_down_since_trim: bool = False  # power cut before background GC ran
    idle_seconds_since_delete: Optional[float] = None
    firmware_claims_zero: bool = False   # drive reports zeros on trimmed LBAs


@dataclass
class ReadSample:
    """One read of an LBA range, captured at a point in time."""

    lba: int
    attempt: int
    sha256: str
    all_zero: bool
    timestamp: float
    nonzero_fraction: float = 0.0   # fraction of bytes that are non-zero (0..1)
    shannon_entropy: float = 0.0    # bits/byte (0..8); high => encrypted/random


@dataclass
class TriageResult:
    verdict: Verdict
    trim_behavior: TrimBehavior
    confidence: float                    # 0..1
    recovery_window_note: str
    rationale: list[str] = field(default_factory=list)
    drive: Optional[DriveFacts] = None

    def to_json(self, indent: int = 2) -> str:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        d["trim_behavior"] = self.trim_behavior.value
        return json.dumps(d, indent=indent)
