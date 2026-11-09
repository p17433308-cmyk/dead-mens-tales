# Workshop — "Scuttled or Seaworthy?" (120 min)

Hands-on, laptop-only. Capacity 25–40. Python 3.9+. No hardware, no root.

## Agenda

| Block | Time | Activity |
|-------|------|----------|
| 0. Setup | 0–10 | Clone BLACKSPOT, `python3 tests/test_triage.py`, confirm green. |
| 1. The lie, demonstrated | 10–25 | Walk through a DZAT capture: drive says zeros, NAND says otherwise. Discuss why. |
| 2. Fingerprinting by hand | 25–45 | Read capture JSON, classify DZAT/DRAT/non-deterministic *before* running the tool; then check against `blackspot`. |
| 3. The decision tree | 45–70 | Each table gets a mystery drive capture. Walk the printed tree, write a verdict + rationale on the worksheet. |
| 4. Defend your verdict | 70–90 | Tables swap verdicts and "cross-examine" each other. Instructor plays hostile defense counsel. |
| 5. The traps | 90–105 | Crypto-erased decoy; a FADING drive where idle time changes the call; a power-cut ALIVE case. |
| 6. Build your own capture | 105–118 | Craft a capture JSON that produces a target verdict — proves they understand the model. |
| 7. Wrap + field kit | 118–120 | Hand out the one-page decision tree; where to send controller fingerprints to grow the dataset. |

## Provided materials
- `samples/` capture packs (DZAT, DRAT, non-deterministic, crypto-erased, power-cut).
- Printed decision tree (see [DECISION_TREE.md](DECISION_TREE.md)).
- Verdict worksheet (drive facts → fingerprint → tree branch → verdict → rationale).

## Learning outcomes
Participants leave able to triage an SSD's recoverability in the field and defend
the call under cross-examination — without a chip-off lab.
