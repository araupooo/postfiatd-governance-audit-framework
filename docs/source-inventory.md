# Source inventory — Consolidated PostFiat Governance-Audit Framework

Pinned postfiatd commit: `0085a1ff885d6a446369cf73a4430f75af22be55`
(2026-10-10, merge of PR #50, "hotfix/upstream-hardening-1.0.9").
All postfiatd paths below are relative to that commit, in repository
`postfiatorg/postfiatd`.

## How the citations were verified

Line numbers were read with `grep -n` / `sed -n` on a local checkout
of the pinned commit — never from a raw-file fetch. The `blob SHA`
column is the local `git hash-object` value for the file at that
commit (the same SHA-1 git assigns to the blob); `size` is the byte
count. The GitHub API cross-check that would independently confirm
these blobs returned HTTP 403 (rate-limited for the shared egress IP)
at build time on 2026-11-25, for both the tree endpoint and the
commits endpoint — that limitation is recorded here rather than
hidden. The pack's own files are proven instead by the fresh-clone
reproduction (see `outputs/fresh-clone-reproduction.log`).

## postfiatd source files (pinned commit)

| File | Lines | Blob SHA (local) | Size | Cited spans |
|---|---|---|---|---|
| `src/xrpld/app/misc/detail/AmendmentTable.cpp` | 1084 | `b13e40c3aed1ec8dbd9ec68a464caa5f512f113f` | 34890 | computeThreshold 323-342; passes() 360-378; veto config parse 600-621; wallet.db vote read 628-650; unknown amendment effectively vetoed 648; veto()/unVeto() 736-762; enable() 763-780; doVoting 851-940 (tfGotMajority 908, tfLostMajority 914, enable action 923); vetoed display 1013-1015 |
| `src/xrpld/app/misc/detail/ValidatorList.cpp` | 2193 | `861e2112c1f9355e03b9e42a7565cf6f37cf8c2e` | 72746 | genesis quorum 126-133; listThreshold_ 197-215; publisher expiry 277-278, 961-985; validation_quorum RPC 1649; calculateQuorum 1845-1935 (67% comment 1898-1900, 60% floor 1931-1935) |
| `src/xrpld/app/misc/FeeVoteImpl.cpp` | 345 | `85b5791d675a287ff2ceafb6f786768cbeac7889` | 10944 | VotableValue::getVotes 70-85; doValidation 120-196; doVoting 196-280 (flag-ledger assert 201-204) |
| `src/xrpld/app/misc/Manifest.h` | 561 | `eb887b8166b45be76142eda2b66f6441935e087f` | 17676 | manifest concept (master + ephemeral key + sequence) 44-76; masterKey 87-88; sequence 96-97; revoked() 133-141 |
| `include/xrpl/protocol/SystemParameters.h` | 95 | `48202928205df69ede2398618420d5585d82b3c4` | 3242 | pre-fix 204/256: 81-83; post-fix 67/100: 85; default majority time 2 weeks: 88 |
| `include/xrpl/protocol/detail/features.macro` | 165 | `a88ebd1a492b9b5d658bde9c5f2835094536b244` | 10479 | fixAmendmentMajorityCalc Supported::yes, DefaultYes: 104; no PostFiat-specific (PFTL / ML-DSA / Cobalt) amendment entries anywhere in the file |
| `src/xrpld/app/main/Application.cpp` | — | `e6ca17172f5213cc5e7c51df9a546a587f62e607` | 68679 | make_AmendmentTable with config().AMENDMENT_MAJORITY_TIME 1286-1292; standalone mode 305; replay ledger load 2027-2074 |
| `src/xrpld/app/ledger/Ledger.cpp` | — | `26552704258627756361a07e0c85a260ed229321` | 33022 | isFlagLedger / isVotingLedger 970-985 |
| `src/xrpld/app/ledger/Ledger.h` | 483 | `552f59ff19c171d8e216b2761cc0a4e8f928f1dd` | 12026 | FLAG_LEDGER_INTERVAL = 256: 426 |
| `src/xrpld/core/Config.h` | 403 | `06cd0d24d8630d55affbbbf76ddcf766863659fc` | 13386 | FeeSetup defaults (reference fee 10 drops, account reserve 10 XRP, owner reserve 2 XRP) 66-81; AMENDMENT_MAJORITY_TIME = defaultAmendmentMajorityTime: 248 |
| `src/xrpld/core/detail/Config.cpp` | 1251 | `19b33b251ab2aeacee5aede6d8746aba6dea4ee6` | 43477 | [amendment_majority_time] parsing 872-895; 15-minute minimum 895 |
| `src/xrpld/app/misc/NegativeUNLVote.h` | 218 | `72ed96571786b70f567e181f7a1cddebc10c4416` | 7430 | low water 50%: 56; high water 80%: 62; min local validations 90%: 69; new-validator skip 2 flag ledgers: 74; max 25% listed: 78 |
| `src/xrpld/app/misc/ValidatorExclusionManager.h` | — | `c1d9dd31335734a0935162490df28d1ec93d0895` | 4166 | exclusion manager interface (configured + remote lists) |
| `src/xrpld/app/misc/ValidatorVoteTracker.h` | — | `a37e8f93d670bca1fec7e9edb96d3180b1496cce` | 2555 | ValidatorVote pseudo-transactions, votes by ledger 24-46 |
| `src/xrpld/app/misc/ValidatorList.h` | 988 | `b610dd81dc479895973ed48756e1803f93b3c95c` | 30156 | ValidatorList interface |

## postfiatd documentation (pinned commit)

| File | Lines | Blob SHA (local) | Size | Cited spans |
|---|---|---|---|---|
| `docs/AmendmentDevelopment.md` | 135 | `cb29663b0d157f05110c17202790ebd5bf5b0667` | 4672 | activation "Once 67% of trusted validators vote yes for 2 weeks": 72; DefaultNo strategy 60-72; DefaultYes strategy 74-90; retirement 96-104 |
| `docs/Exclusions.md` | 347 | `f5a818a5d1e2b39c751efd401083db7a3f235748` | 10927 | 67% agreement to exclude: 5; one change per 10 ledgers: 41; threshold 67% (minCONSENSUS_PCT): 184; rate: 191 |
| `docs/DeploymentWorkflows.md` | 314 | `47ca2649fddcaae75dab33bf98d85bd4eb7c20ac` | 13686 | workflow table (Update: pull latest image and restart): 18; validators deploy sequentially, max-parallel 1: 85; Update Nodes: 102-104 |
| `docs/0010-ledger-replay/README.md` | — | `c82d9b1906da1412677673b6b7f2942a1051dd1d` | 4577 | LedgerReplayer design (per-node re-execution; three worker types) |
| `docs/0001-negative-unl/README.md` | — | `f28ff63c6f051ad147a0fcba7de049b06bc7d6f0` | 29033 | negative UNL problem statement and on-ledger design |

## External primary sources

| Source | What was verified | When / how |
|---|---|---|
| xrpl.org, "Amendments" (`https://xrpl.org/docs/concepts/networks-and-servers/amendments`) | ">80% support for two weeks" and "Disabling a passed amendment requires a new amendment to do so" (L7-8); flag ledger every 256th ledger (L21); tfGotMajority / tfLostMajority / enable (L27-40); "Amendments that have had their source code removed without being enabled are considered Vetoed" (L59); amendment-blocked servers (L63-80); retirement after 2 years, XLS-11 (L92-98) | Re-fetched and read in full 2026-11-25 (133 lines) |
| PostFiat whitepaper (`https://postfiat.org/whitepaper/`) | "treasury": 0 occurrences; "amend": 0 occurrences (verified absences, full-text find over 677 lines). "every native fee burns, no validator reward exists" (§1.1); "Loss of quorum halts the chain rather than lowering q" (§1.8); q=24 of 35 (§1.8, §1.11); "Cobalt ratifies scoped validator-trust updates" (§1.8/§1.9); ML-DSA-65 from genesis (§1.11) | Fetched 2026-11-25 (677 lines) for the absence checks; §1.8/§1.11 claims verified 2026-11-15 in the prior amendment research pass (see docs/research-notes.md) |
| NIST FIPS 204 / FIPS 205 / IR 8547 | ML-DSA / SLH-DSA parameter sets and sizes; deprecate-after-2030 / disallow-after-2035 timeline (context for the quantum-exposure note in the findings) | Direct PDF text extraction 2026-11-16 (prior research pass) |
| XRPL Labs disclosure reports (Batch, Feb 2026; xrpld 3.4.1, Oct 2026) | Pre-activation veto as the working safety valve; a critical fix shipped as a direct change bypassing the amendment vote | Prior research pass (see docs/research-notes.md for status tags) |

## Verified absences (stated as absences, not as claims about the world)

- "treasury": 0 hits, case-insensitive, across all of `src/` in the
  pinned checkout; 0 hits in the live whitepaper (677 lines,
  2026-11-25). No treasury mechanism exists to audit.
- "amend": 0 hits in the live whitepaper. Amendment rules live only
  in code and in `docs/AmendmentDevelopment.md`, not in the
  whitepaper.
- "cobalt": 0 hits, case-insensitive, across `src/` and `include/`
  in the pinned checkout. The whitepaper's Cobalt ratification has no
  counterpart in the assessed code; validator-trust updates go through
  publisher lists (`ValidatorList.cpp`) instead.
- No PostFiat-specific amendment entries in `features.macro` (no
  PFTL / ML-DSA / Cobalt entries). The fork's amendment set is the
  inherited XRPL set.
- No scheduled-upgrade mechanism in code: `upgrade` appears in only
  3 files under `src/xrpld/app` (LedgerMaster, NetworkOPs — ledger
  application, not a scheduled upgrade). Upgrades are binary rollouts
  (`docs/DeploymentWorkflows.md`) plus amendment votes.
- No rollback path for an enabled amendment in code, and no primary
  source describing a rolled-back activated amendment was found
  (searched, not found — see docs/research-notes.md §5.4).

## Reused prior work (not re-derived here)

The amendment-threshold findings reuse the verified amendment
research of 2026-11-16 (prior pack research pass): the pre-fix
204/256 vs post-fix 67/100 constants, the `>=` vs `>` comparison,
the fix amendment's registration, and the upstream 80% comparison.
That pass is summarised with its status tags in
`docs/research-notes.md`; this pack re-verified every constant and
line number it cites on the local checkout at 0085a1ff rather than
copying line numbers from that pass.
