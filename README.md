# Consolidated PostFiat Governance-Audit Framework

A consolidated governance-audit framework for postfiatd at pinned
commit `0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10),
covering five domains: amendment quorum and veto behaviour,
validator-set governance and key compromise, treasury and fee
controls, upgrade procedures, and rollback procedures.

## Reproduce this pack

```bash
bash scripts/run_all.sh
```

Expected: exit 0, `outputs/` reproduced byte-for-byte (excluding
`outputs/run_all.log`), `verify_digests.sh` reports all digests OK.

The committed fresh-clone reproduction transcript is
`outputs/fresh-clone-reproduction.log` — it records a clean-checkout
run of the command above, the digests check, and the manifest SHA
matching the committed `manifest.json`.

## What this pack contains

- `scenarios/` — 11 governance edge-case scenarios (G0–G10):
  quorum failure, veto deadlock, compromised validator keys,
  emergency upgrade with rollback, treasury/fee gaps, publisher
  churn, majority-loss clock restart, fee-vote splits,
  amendment-blocked divergence, majority-time override.
- `scripts/` — the deterministic harness (`simulator.py`,
  `load_harness.py`), matrix/control builders, manifest + digest
  tooling, and the `run_all.sh` reproduction driver.
- `outputs/` — unedited harness outputs for all 11 scenarios (JSON +
  CSV), `controls.json`/`controls.csv`, `matrix.json`/`matrix.csv`,
  and the fresh-clone reproduction transcript.
- `docs/` — source inventory (every cited file:line with blob SHA),
  control inventory, methodology, ranked findings, operator
  remediation, decision memo, environment, research notes.

## Headline results (all SIMULATED by the harness)

- Severity: **1 HIGH, 6 MEDIUM, 3 LOW, 1 INFO**.
- Controls: **19 total — 15 MEASURED, 1 PARTIAL, 3 UNMEASURED**.
- HIGH: an enabled amendment cannot be rolled back (G4) — the only
  fix-forward paths are a new amendment or a binary upgrade.
- The 14-day hold is too slow for an active exploit (G4) — the
  emergency path is a binary upgrade.
- A minority can pass an amendment during a partial outage (G1): 12
  validators offline for 5 days, 108,000 ledgers missed, and the
  23-vote minority gained majority because the threshold denominator
  is validations received, not UNL size.
- 12 vetoes stall an amendment indefinitely (G2); a 2-hour support
  dip costs 12 banked days (G7); 5 amendment-blocked validators cut
  the safety margin from 11 to 6 (G9); the 14-day hold can be
  shortened to 15 minutes by an operator config change (G10).
- No treasury mechanism exists (G5): 0 hits in code, 0 in the
  whitepaper — fee votes are the only economic control, and they
  stall on splits (G5, G8).

## Claim-to-evidence index

| Claim | Script | Raw output | Primary source |
|---|---|---|---|
| 67% threshold, strict `>` (post-fix) | `scripts/simulator.py` (compute_threshold) | `outputs/G0-baseline-full-governance.json` | `SystemParameters.h:81-88`; `AmendmentTable.cpp:323-342, 360-378` |
| Threshold denominator = validations received | `scripts/simulator.py` | `outputs/G1-quorum-failure-minority-majority.json` | `AmendmentTable.cpp:93-108, 267-276, 351` |
| 14-day hold, clock restarts on loss | `scripts/simulator.py` (doVoting) | `outputs/G7-majority-loss-clock-restart.json` | `SystemParameters.h:88`; `AmendmentTable.cpp:886-923`; xrpl.org Amendments |
| Veto persists until un-vetoed | `scripts/simulator.py` | `outputs/G2-veto-deadlock.json` | `AmendmentTable.cpp:600-621, 736-762` |
| Manifest rotation / revocation | `scripts/simulator.py` | `outputs/G3-compromised-validator-key.json` | `Manifest.h:44-76, 133-141` |
| 67% validation quorum, 60% floor | `scripts/simulator.py` (calculate_quorum) | `outputs/G6-publisher-churn-negative-unl.json` | `ValidatorList.cpp:1898-1935` |
| Fee vote: most-voted value, ties keep current | `scripts/simulator.py` (VotableValue) | `outputs/G5-treasury-fee-gap.json`, `outputs/G8-fee-vote-split-reserves.json` | `FeeVoteImpl.cpp:70-85, 196-280` |
| No rollback path | `scripts/simulator.py` (attempt_rollback) | `outputs/G4-emergency-upgrade-no-rollback.json` | xrpl.org Amendments ("Disabling a passed amendment requires a new amendment") |
| No treasury | — (verified absence) | `outputs/G5-treasury-fee-gap.json` | 0 hits for "treasury" in `src/` and in the whitepaper |
| Majority-time override to 15 min | `scripts/simulator.py` | `outputs/G10-majority-time-override.json` | `Config.h:248`; `Config.cpp:872-895` |
| Amendment-blocked enforcement | `scripts/simulator.py` | `outputs/G9-amendment-blocked-divergence.json` | xrpl.org Amendments ("Amendment Blocked Servers") |

Every matrix row in `outputs/matrix.json` also carries an
`output_path` field pointing at its committed raw output, so any
headline claim is spot-checkable without this index.

## OBSERVED vs SIMULATED

- **OBSERVED** = read directly from a primary source (a file:line in
  the pinned checkout, a fetched page, or a counted search result).
  OBSERVED claims carry their citation.
- **SIMULATED** = produced by the harness. Every number in
  `outputs/G*.json`, `outputs/matrix.json`, and
  `outputs/controls.json` is SIMULATED: the parameters, gates, and
  thresholds are the pinned code's; the validator behaviour, vote
  splits, outages, and key events are deterministic stand-ins. No
  live postfiatd node was run (see `docs/environment.md`).

## Pinned source

- postfiatd commit `0085a1ff885d6a446369cf73a4430f75af22be55`
  (2026-10-10, merge of PR #50). All cited line numbers were read
  from a local checkout of that commit; blob SHAs are in
  `docs/source-inventory.md`.
- The amendment-threshold findings reuse the verified amendment
  research of 2026-11-16 (see `docs/research-notes.md`); every
  constant and line number cited here was re-verified on the
  checkout, not copied.

## Limitations

- No live node was run; no live network was observed. Whether the
  post-fix 67% threshold has activated on any live PostFiat network
  is UNVERIFIED (needs a live ledger Amendments-object check).
- The GitHub API tree/commits endpoints returned HTTP 403
  (rate-limited) at build time, so blob SHAs are local
  `git hash-object` values rather than API-confirmed.
- One ledger close = 4 s virtual time (a modeling choice); flag
  ledgers are evaluated on virtual time during outages, where the
  real network would close no ledgers. See `docs/methodology.md`
  and `docs/environment.md` for the full list.
