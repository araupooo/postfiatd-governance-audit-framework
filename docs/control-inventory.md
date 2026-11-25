# Control inventory — Consolidated PostFiat Governance-Audit Framework

Pinned postfiatd commit: `0085a1ff885d6a446369cf73a4430f75af22be55`.
Status: **MEASURED** = exercised by the harness in the listed
scenarios; **PARTIAL** = exercised with a coverage gap (stated in the
measurement); **UNMEASURED** = no harness path exists (the control is
absent, or the harness models no transaction flow for it). Full
measurements with computed numbers are in `outputs/controls.json` /
`.csv`; this file is the human-readable inventory with the source
citation for each control.

## Domain 1 — Amendment quorum and veto

| ID | Control | Source | Scenarios | Status |
|---|---|---|---|---|
| C00 | Post-fix 67% amendment threshold, strict `>` (pre-fix 204/256 with `>=`; one-validator `>=` exception) | SystemParameters.h:81-88; AmendmentTable.cpp:323-342, 360-378 | G0,G1,G2,G7,G10 | MEASURED |
| C01 | 2-week majority hold before enablement | SystemParameters.h:88; Config.h:248; AmendmentTable.cpp:886-923 | G0,G7 | MEASURED |
| C02 | Flag-ledger voting cadence (every 256 ledgers) | Ledger.h:426; Ledger.cpp:970-985 | G0 | MEASURED |
| C03 | Veto by config (`[veto_amendments]`) with persisted vote | AmendmentTable.cpp:600-621, 736-762 | G2 | MEASURED |
| C04 | Unknown amendment effectively vetoed | AmendmentTable.cpp:648 | G2 | MEASURED |
| C05 | DefaultYes / DefaultNo vote behaviour | features.macro:104; AmendmentDevelopment.md:60-90 | G0,G4 | MEASURED |

## Domain 2 — Validator-set governance and key compromise

| ID | Control | Source | Scenarios | Status |
|---|---|---|---|---|
| C06 | 67% validation quorum with 60% absolute floor | ValidatorList.cpp:1898-1935 | G0,G1,G3,G6 | MEASURED |
| C07 | Quorum disabled when too many publishers are unavailable | ValidatorList.cpp:1861-1893 | G6 | MEASURED |
| C08 | Publisher listThreshold (1 if <3 publishers, else N/2+1) | ValidatorList.cpp:197-215 | G6 | MEASURED |
| C09 | Manifest rotation (higher sequence supersedes) | Manifest.h:44-76, 87-97 | G3 | MEASURED |
| C10 | Master-key revocation (sequence 0xFFFFFFFF) | Manifest.h:133-141 | G3 | MEASURED |
| C11 | Negative UNL (unreliable validators lower the effective UNL) | NegativeUNLVote.h:50-80; docs/0001-negative-unl/README.md | G6 | MEASURED |
| C12 | Validator exclusion (67% agreement, one change per 10 ledgers) | docs/Exclusions.md:5, 41, 184, 191 | G6 | MEASURED |

## Domain 3 — Treasury and fee controls

| ID | Control | Source | Scenarios | Status |
|---|---|---|---|---|
| C13 | Fee vote (trusted-only, flag ledger, most-voted value) | FeeVoteImpl.cpp:70-85, 196-280 | G5,G8 | PARTIAL |
| C14 | Fee burn / no validator subsidy | Whitepaper Abstract, §1.1 | — | UNMEASURED |
| C15 | Treasury control | ABSENT (0 hits in src/ and in the whitepaper) | G5 | UNMEASURED |

## Domain 4 — Upgrade procedures

| ID | Control | Source | Scenarios | Status |
|---|---|---|---|---|
| C16 | Sequential validator rollout (max-parallel 1) | docs/DeploymentWorkflows.md:18, 85, 102-104 | G4,G9 | MEASURED |
| C17 | Amendment-blocked enforcement | AmendmentTable.cpp:648, 1013-1015; xrpl.org Amendments | G4,G9 | MEASURED |

## Domain 5 — Rollback procedures

| ID | Control | Source | Scenarios | Status |
|---|---|---|---|---|
| C18 | Amendment rollback | ABSENT (no path in code; xrpl.org: new amendment only) | G4 | UNMEASURED |

## Totals

19 controls: **15 MEASURED, 1 PARTIAL (C13), 3 UNMEASURED
(C14, C15, C18)**.

## Notes on the unmeasured controls

- **C14 (fee burn):** the harness submits no transactions, so no fee
  is collected or burned in any scenario. The invariant is OBSERVED
  only — the whitepaper states "every native fee burns, no validator
  reward exists". The code path that destroys collected fees was not
  traced to a single function in this pack; do not cite C14 as
  harness-verified.
- **C15 (treasury):** there is no mechanism to exercise. The absence
  itself is the finding, verified by exhaustive search (0 hits for
  "treasury" in `src/` and in the 677-line whitepaper).
- **C18 (amendment rollback):** there is no mechanism to exercise.
  The absence itself is the finding, verified against the code (no
  rollback path) and the xrpl.org statement that disabling a passed
  amendment requires a new amendment.

## Notes on the partial control

- **C13 (fee vote):** the most-voted-value rule moves a fee only on a
  modal majority. G5 (12/12/11 split) and G8 (18/17 split) both show
  a field stalling even though a majority of voters want some change.
  The control works as coded; its coverage gap is that a split field
  cannot move, which is a governance property, not a bug.
