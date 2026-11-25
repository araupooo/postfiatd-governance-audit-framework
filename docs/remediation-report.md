# Operator remediation — Consolidated PostFiat Governance-Audit Framework

Pinned postfiatd commit: `0085a1ff885d6a446369cf73a4430f75af22be55`.
Every item maps to a finding in `docs/findings-report.md` and a
control in `docs/control-inventory.md`. Items are ordered by the
finding severity they address. Nothing here requires a code change to
the assessed commit unless marked [CODE].

## HIGH

### R1 — Treat activation as irreversible: pre-activation checklist (F1, F2)

Before any amendment reaches majority, complete and record:

1. The amendment's code has been reviewed by at least two independent
   reviewers and the review is recorded.
2. A rollback-by-new-amendment is drafted in advance (the replacement
   amendment's identifier and vote plan), so the fix-forward path
   does not start from zero.
3. The emergency binary-upgrade path is tested: a canary validator
   upgrades, re-syncs, and re-validates without a restart loop.
4. Veto count is monitored; any veto count ≥ 6 triggers a governance
   review before enablement (see R4).

[RISK] The 14-day hold is the last brake. If a faulty amendment
enables, there is no undo — only a second 14-day hold (or a forced
binary upgrade).

### R2 — Publish an emergency-upgrade runbook (F2)

1. Pre-stage upgrade packages so a critical binary can reach all
   validators within hours, not days.
2. Define the go/no-go criteria for bypassing the amendment process
   (the xrpld 3.4.1 precedent: a Critical payment-engine overflow
   shipped as a direct change because the vote was too slow).
3. Define who declares the emergency, who approves the bypass, and
   how the decision is recorded — before an incident, not during one.
4. After an emergency upgrade, audit the amendment-blocked set and
   confirm every validator is back on the current binary before
   resuming normal amendment voting.

## MEDIUM

### R3 — Watch amendment majorities during outages (F3)

1. Alert when the trusted-validations count drops below UNL size
   while any amendment holds a majority: the threshold has shrunk and
   a minority may be passing.
2. Do not let an outage last the full 14-day hold with an amendment
   at majority — restore validators or use vetoes to pause the
   amendment before the hold completes.
3. After recovery, re-check every amendment's majority status against
   the full UNL count, not the outage count.

[CODE] Consider a code gate that freezes amendment-majority counting
while the network is below validation quorum. This does not exist in
the assessed code; it is a proposed change, not an existing control.

### R4 — Treat vetoes near 12 as a governance incident (F4)

1. Alert at 6 vetoes on any amendment; escalate at 10.
2. At 12 vetoes the amendment cannot enable — record the blocking
   positions and the path to resolution (persuasion, a revised
   amendment, or a binary-upgrade bypass).
3. Review vetoed amendments quarterly; a veto with no recorded reason
   is a governance gap.

### R5 — Keep support well above the bar until enablement (F5)

1. Target support ≥ 30 of 35 (not 24-25) until the amendment enables.
2. Avoid validator restart waves, config changes, and maintenance
   windows during the final 2 days of a hold.
3. If support dips, expect the enablement date to slip by the full
   banked period — re-plan, do not assume partial credit.

### R6 — Do not assume treasury controls exist (F6)

1. Any treasury design must be built and governed from scratch; there
   is no existing on-chain treasury, spending policy, or governance
   path in the assessed code.
2. Until a treasury exists, fee votes are the only economic control —
   coordinate an explicit modal position before proposing a fee change
   (see R10).

### R7 — Prune persistently amendment-blocked validators (F7)

1. Alert when a validator is amendment-blocked for more than 7 days.
2. Remove persistently blocked validators from the publisher lists so
   the quorum math reflects the live set; re-add them after they
   upgrade.
3. Track the safety margin (online validators minus quorum) as a
   dashboard metric; alert when it falls below 8.

### R8 — Treat the majority-time hold as a governance parameter (F8)

1. Agree the hold network-wide (default 14 days) and record it as a
   governance decision, not a local config choice.
2. Audit `[amendment_majority_time]` across all validators at least
   quarterly; any value below 14 days is a governance incident.
3. [CODE] Consider removing the operator override or requiring a
   supermajority of operators to change it.

## LOW

### R9 — Tested key-compromise runbooks (F9)

1. Signing-key compromise: rotate the manifest (sequence+1) and
   verify the new ephemeral key is validating within one flag-ledger
   interval. Test this quarterly on a non-production validator.
2. Master-key compromise: revoke (sequence 0xFFFFFFFF), confirm the
   validator leaves the UNL, and stand up a pre-staged replacement
   validator with a new master key. Note: revocation is irreversible.
3. Keep master keys offline; never reuse a master key after
   revocation.

### R10 — Coordinate fee votes explicitly (F11)

1. Before proposing a fee change, agree a single modal value and get
   explicit buy-in from a majority of trusted validators.
2. Require every trusted validator to submit a fee field (no silent
   noVote) during a fee-change window.
3. After a fee change, verify the new fee is in effect at the next
   flag ledger; if the vote split, record the split and re-propose
   with a single modal value.

### R11 — Publisher diversity (F10)

1. Three publishers minimum, operated by independent parties on
   independent hosting.
2. Alert on any single publisher outage; escalate when two are down
   (the chain halts).
3. Test the negative-UNL path: confirm unreliable validators are
   detected and excluded within the documented thresholds.

## Verification

Each remediation can be checked against the pack:

- R3/R5/R8: re-run the harness with the scenario parameters changed
  (`scripts/load_harness.py`, `scripts/simulator.py`).
- R1/R2/R4/R6/R7/R9/R10/R11: operational procedures — verify by
  inspection against the cited sources in
  `docs/source-inventory.md`.
