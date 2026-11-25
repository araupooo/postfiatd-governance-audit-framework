# Research notes — Consolidated PostFiat Governance-Audit Framework

## 1. What this pack reuses (not re-derived)

This pack reuses the verified amendment research of 2026-11-16 (the
prior amendment-activation research pass; full record in the prior
pack's `SOURCES.md`, 456 lines). That pass established, from the
pinned postfiatd code at the same commit family:

- The pre-fix amendment threshold 204/256 (79.6875%) with `>=`
  comparison, and the post-fix 67/100 threshold with strict `>`
  (one-validator `>=` exception) — `SystemParameters.h:81-88`,
  `AmendmentTable.cpp:323-342, 360-378`.
- `fixAmendmentMajorityCalc` registered as `Supported::yes` with
  `VoteBehavior::DefaultYes` (`features.macro:104`).
- The upstream XRPL 80% comparison (xrpl.org: ">80% support for two
  weeks"), the flag-ledger mechanics (every 256th ledger), and the
  tfGotMajority / tfLostMajority flags.
- The ML-DSA-65-from-genesis whitepaper claim and the Cobalt
  ratification description.

This pack re-verified every constant and line number it cites on the
local checkout at `0085a1ff` rather than copying line numbers from
that pass. Line numbers in this pack are therefore current to the
pinned commit; the prior pass's numbers were checked against the same
checkout and agree.

## 2. Status tags

- **VERIFIED** = read directly in the primary source named.
- **SECONDARY** = reported by a news/analysis outlet; the primary
  record was not fetched.
- **UNVERIFIED** = could not be confirmed against a primary source.
- **VERIFIED ABSENCE** = a full-text search of the named source
  returned zero hits (stated as an absence, not as a claim about the
  world).

## 3. The 67% threshold on a live network — UNVERIFIED

Whether `fixAmendmentMajorityCalc` has actually ACTIVATED on any live
PostFiat network is UNVERIFIED. It requires a live ledger
Amendments-object check, which was not performed. This pack assumes
the post-fix rule (67%, strict `>`) because the fix is registered as
`Supported::yes` with `DefaultYes` in the pinned code. Every
threshold-dependent result in this pack is therefore conditional on
that assumption; if a live network still runs the pre-fix rule, the
threshold is 204/256 (79.6875%) with `>=`, and G1/G9's denominator
arithmetic changes accordingly (the mechanism — denominator =
validations received — is the same under both rules).

## 4. Whitepaper

Source (primary): PostFiat, *A Buy-Side Internet of Value*,
`https://postfiat.org/whitepaper/`.

- **VERIFIED (2026-11-15 pass):** q=24 of 35 (§1.8, §1.11); "Loss of
  quorum halts the chain rather than lowering q" (§1.8); "Cobalt
  ratifies scoped validator-trust updates; a live update requires a
  decision ratified by Cobalt, q=24/35" (§1.8/§1.9); "ML-DSA-65 from
  genesis" (§1.11); "every native fee burns, no validator reward
  exists" (Abstract, §1.1); "one organization administers the current
  validator fleet" (§1.8); "Several requirements remain proposals:
  ... emergency redemption path ... independently operated
  validators."
- **VERIFIED ABSENCE (re-checked 2026-11-25, full-text find over 677
  lines):** "treasury": 0 occurrences. "amend": 0 occurrences.
  Amendment rules live only in code and in
  `docs/AmendmentDevelopment.md`, not in the whitepaper.
- The paper was re-fetched 2026-11-25 for the absence checks; the
  §1.8/§1.11 claims above are cited from the 2026-11-15 verified
  read. If the paper changes, re-verify those citations.

## 5. Incidents (case studies, not pack evidence)

### 5.1 Incident A — XRPL `Batch` amendment, critical auth flaw caught pre-activation (Feb 2026)

A flaw in the signature-validation logic of the proposed `Batch`
amendment (rippled 3.1.0): an early-exit in the batch-signer check
let an attacker execute inner transactions on behalf of arbitrary
victim accounts. Vetoes were cast the same evening. Emergency release
rippled 3.1.1 (23 Feb 2026) marks both `Batch` and
`fixBatchInnerSigs` as unsupported, preventing activation. A
corrected replacement, `BatchV1_1`, was later proposed.

- **Source (primary):** XRPL Labs, "Vulnerability Disclosure Report:
  XRPL Batch Amendment" (xrpl.org blog, 2026-02-26). **VERIFIED.**
- **Use in this pack:** the veto as the working safety valve (F4,
  R4). The flaw was caught pre-activation because vetoes could be
  cast fast; the 14-day hold gave time.

### 5.2 Incident B — xrpld 3.4.1, payment-engine overflow fix bypassed the amendment vote (Sep–Oct 2026)

Two bugs fixed in xrpld 3.4.1 (released 25 Sep 2026, emergency
release): (1) a Batch variant fix, `fixBatchV1_2`, which activated on
Mainnet 9 Oct 2026 (same day `BatchV1_1` activated); (2) a payment
engine XRP overflow — a Critical fix shipped "as a direct change
rather than an amendment" because the 80%-for-two-weeks wait was
judged too slow. Servers not on 3.4.1+ became amendment-blocked.

- **Source (primary):** "Vulnerability Disclosure Report for xrpld
  3.4.1", xrpl.org blog, published 9 Oct 2026. **VERIFIED** (excerpt
  read in the prior pass; a full-page re-read is owed before verbatim
  quotation of any passage beyond the one quoted in §5.2 of the prior
  SOURCES.md).
- The "~18 trillion XRP" figure is SECONDARY (Veria Labs' math, via
  ThreatWire/CoinSpeaker coverage) and is not used in this pack.
- **Use in this pack:** the emergency-upgrade precedent (F2, R2).
  The amendment process is not the emergency path; the binary upgrade
  is.

### 5.3 Incident C — fixCleanup3_4_0 lost its majority 12 days in, restarted the 14-day clock (Oct–Nov 2026)

`fixCleanup3_4_0` (xrpld 3.4.0; fixes a PaymentBurn delegation flaw)
lost its majority 12 days into the 14-day hold, and the clock
restarted.

- **Source:** SECONDARY — Unchained, "XRP Ledger Turns On Fix for
  Delegated Burn Permission…" (5 Nov 2026). The ledger date/time
  (Nov 4, 14:52 UTC, ledger 108,112,129) is secondary only.
- **Status:** SECONDARY — usable as a case study only with that
  caveat. Re-verify against the ledger before asserting the dates.
- **Use in this pack:** the real-world analogue of G7 (F5, R5). The
  clock-restart rule itself is VERIFIED from xrpl.org (re-fetched
  2026-11-25): "If support drops below 80%, the amendment is
  temporarily rejected, and the two week period restarts."

### 5.4 Rollback of an activated amendment — UNVERIFIED ABSENCE

No primary source describing a rolled-back activated amendment was
found (searched, not found — absence of evidence, stated as such).
xrpl.org states the only path: "Disabling a passed amendment
requires a new amendment to do so" (re-fetched 2026-11-25). The
Batch cases above were all pre-activation (veto, not rollback).
This pack's G4 models the documented reality: a rollback attempt
fails.

## 5.5 Cobalt — gap between whitepaper and code

The whitepaper describes Cobalt ratification of validator-trust
updates (§1.8/§1.9, q=24/35, activation-height binding). The
assessed code has 0 hits for "cobalt" (case-insensitive) in `src/`
and `include/`, and no PostFiat-specific amendment entries in
`features.macro`. Validator-trust updates in the assessed code go
through publisher lists (`ValidatorList.cpp`) instead. This is a
gap finding, not a claim that Cobalt does not exist anywhere — it
does not exist in the assessed code. Whether Cobalt is implemented
elsewhere (another repo, a future release) is UNVERIFIED.

## 6. Quantum-exposure context (background, not a pack finding)

NIST FIPS 204 (ML-DSA) and FIPS 205 (SLH-DSA) are final; NIST IR
8547 deprecates RSA/ECDSA after 2030 and disallows them after 2035.
PostFiat signs accounts and validators with ML-DSA-65 from genesis
(whitepaper §1.11, VERIFIED in the prior pass). The whitepaper does
NOT state that amendment votes specifically are ML-DSA-signed — that
is UNVERIFIED and is not claimed in this pack. The quantum-exposure
note matters for the validator-set governance domain only in that
manifest key management (C09, C10) is the mechanism that would carry
a post-quantum key rotation; the pack does not re-audit the
cryptography.

## 7. Open items (re-verify before citing)

- Whether `fixAmendmentMajorityCalc` has activated on any live
  PostFiat network (live ledger Amendments-object check).
- Whether postfiatd's runtime config overrides
  `defaultAmendmentMajorityTime` on any live network (operator
  configs are not public).
- Incident C dates/ledger (Nov 4, 14:52 UTC, ledger 108,112,129) —
  secondary only.
- Full-page re-read of the xrpld 3.4.1 disclosure before verbatim
  quotation beyond the excerpt in the prior SOURCES.md.
- The whitepaper's §1.8/§1.11 citations if the paper is updated
  after 2026-11-25.
