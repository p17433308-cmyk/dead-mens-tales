# Novelty & Prior-Art Delta

A pre-emptive answer to the reviewer question: *"what's new here vs. the existing
SSD-forensics body of work?"*

## The existing body of work

| Work | What it establishes | What it does NOT do |
|------|--------------------|---------------------|
| Wei et al. 2011, *Reliably Erasing Data from Flash-Based SSDs* (USENIX FAST) | Software overwrites leave large fractions of data intact in over-provisioning; only hardware block-erase is reliable. | No investigator-facing triage; measured via NAND-level access, not host-side. |
| Bell & Boddington 2010, *Empirical analysis of SSD data retention* | TRIM/GC make deleted data often unrecoverable; outcome is controller-dependent. | Descriptive; no tool; no decision procedure. |
| Scanlon et al., *SSD Forensics: Where Do We Stand?* | Surveys non-deterministic TRIM and the FTL's disruption of logical↔physical mapping. | Survey, not a method or tool. |
| arXiv 2307.10192 (2023), *SSD Forensic: Evidence Generation…* | Recovery viable when TRIM disabled; vendor-dependent persistence. | Lab experiments; no released triage tooling. |
| ElcomSoft 2025, *What TRIM, DRAT, DZAT really mean* | DZAT drives return zeros while NAND may still hold data. | Vendor commentary; no open tool; no verdict framework. |
| PC-3000 / commercial labs | FTL reconstruction from raw NAND (chip-off). | Proprietary, destructive, expensive, lab-only. |
| UBIFT (DFRWS 2024) | Open-source forensics for raw-flash **UBIFS**. | Not SSD FTLs; different storage class. |

## Our delta (one line)

> **Prior work proves remnants persist and that chip-off can reach them. We ship
> the missing decision layer: the first open-source, host-side tool that
> fingerprints controller post-TRIM behavior, detects DZAT masking ("the drive is
> lying"), and classifies recoverability into a court-defensible verdict —
> *before* a destructive chip-off.**

## Three concrete, defensible contributions
1. **Controller behavior as evidence.** Formalizes DZAT/DRAT/non-deterministic
   classification from reproducible read maps, and treats a masking drive as a
   positive finding rather than a dead end.
2. **An auditable recoverability decision tree** where every branch maps to a
   physically true statement — survivable under cross-examination.
3. **The first open-source host-side SSD triage tool (BLACKSPOT)** + shareable
   capture-pack format, enabling a crowd-sourced controller-fingerprint dataset.

## What we explicitly DO NOT claim
- We do **not** recover garbage-collected or over-provisioned pages host-side.
  Once a controller erases a physical page, the host path cannot address it. That
  is the entire reason chip-off exists; we respect the physics and say so on stage.
- We do **not** defeat crypto-erase. A confirmed SED crypto-erase ends recovery.
