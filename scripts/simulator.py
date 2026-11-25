#!/usr/bin/env python3
"""simulator.py — faithful protocol-level simulator of PostFiat
governance: amendment quorum and veto, validator-set governance and
key compromise, treasury and fee controls, upgrade procedures, and
rollback procedures.

Pinned postfiatd commit: 0085a1ff885d6a446369cf73a4430f75af22be55.
Every control parameter below is taken verbatim from the pinned code;
each is traced to its exact file:line in docs/source-inventory.md.

The simulator does NOT build or run postfiatd. It re-implements the
decision logic of the cited functions over a modeled validator set, so
the measured outcomes are SIMULATED (see docs/methodology.md). The
parameters, gates, thresholds, and order of operations are the pinned
code's; the validator behaviour, vote splits, outages, and key events
are deterministic stand-ins.

Determinism: no wall clock, no random module. One ledger close = 4 s
of virtual time (a modeling choice; the pinned code does not fix a
close interval). Ledger sequences start at 1,000,000. All counts are
integers; all times are exact multiples of the flag-ledger interval.

Modelled functions (pinned code -> simulator method):
  AmendmentSet::computeThreshold / passes (pre-fix 204/256 >=,
      post-fix 67/100 >, one-validator >= exception)
      -> GovernanceNetwork.amendment_threshold / amendment_passes
         (AmendmentTable.cpp:323-342, 360-378;
          SystemParameters.h:81-88)
  AmendmentTableImpl::doVoting (tfGotMajority / tfLostMajority /
      enable when majority held for majorityTime_)
      -> GovernanceNetwork._do_voting
         (AmendmentTable.cpp:851-940)
  AmendmentTableImpl::veto / unVeto (persist vote)
      -> GovernanceNetwork.veto / unveto
         (AmendmentTable.cpp:736-762)
  [veto_amendments] / [amendments] config parsing; unknown
      amendments effectively vetoed
      -> GovernanceNetwork._vetoed_state
         (AmendmentTable.cpp:600-650)
  AmendmentTableImpl::enable
      -> GovernanceNetwork._enable (AmendmentTable.cpp:763-780)
  Ledger::isFlagLedger / isVotingLedger (every 256th ledger)
      -> GovernanceNetwork._flag_ledgers_in
         (Ledger.h:426; Ledger.cpp:970-985)
  Config AMENDMENT_MAJORITY_TIME (default 2 weeks, overridable
      down to 15 minutes)
      -> GovernanceNetwork.majority_hold_days
         (Config.h:248; Config.cpp:872-895;
          SystemParameters.h:88)
  ValidatorList::calculateQuorum (67% of effective UNL, 60% floor
      of original UNL; disabled when too many publishers unavailable)
      -> GovernanceNetwork.validation_quorum
         (ValidatorList.cpp:1845-1935)
  ValidatorList listThreshold_ (1 if <3 publishers, else N/2+1)
      -> GovernanceNetwork.list_threshold
         (ValidatorList.cpp:197-215)
  ValidatorList publisher expiry / stale lists; config-listed keys
      never expire
      -> GovernanceNetwork._publisher_state
         (ValidatorList.cpp:51-64, 277-278, 961-985)
  Manifest (master key + ephemeral signing key + sequence;
      revoke via sequence 0xFFFFFFFF)
      -> GovernanceNetwork.rotate_manifest / revoke_manifest
         (Manifest.h:44-76, 87-97, 133-141)
  NegativeUNL thresholds (50/80/90% of flag interval)
      -> GovernanceNetwork._negative_unl_adjust
         (NegativeUNLVote.h:57-74; docs/0001-negative-unl/README.md)
  Validator exclusion (67% agreement, one change per 10 ledgers)
      -> GovernanceNetwork._exclusion_step
         (docs/Exclusions.md:5, 41, 184, 191)
  FeeVoteImpl::doVoting (flag ledger only, trusted validators
      only) + VotableValue::getVotes (most-voted value between
      current and target, inclusive)
      -> GovernanceNetwork._fee_vote
         (FeeVoteImpl.cpp:70-85, 196-280)
  FeeSetup defaults (reference fee 10 drops, account reserve
      10 XRP, owner reserve 2 XRP)
      -> GovernanceNetwork.fees (Config.h:66-81)
  Deployment workflows: Update pulls the latest image and restarts;
      validators deploy sequentially (max-parallel 1)
      -> GovernanceNetwork.binary_upgrade
         (docs/DeploymentWorkflows.md:18, 85, 102-104)
  Amendment-blocked servers (no code for an enabled amendment)
      -> GovernanceNetwork._blocked_validators
         (xrpl.org Amendments, "Amendment Blocked Servers";
          AmendmentTable.cpp:648, 1013-1015)
  Ledger replay (per-node re-execution; LedgerReplayer)
      -> GovernanceNetwork.ledger_replay
         (docs/0010-ledger-replay/README.md;
          Application.cpp:2027-2074)
"""

import math

PINNED_COMMIT = "0085a1ff885d6a446369cf73a4430f75af22be55"

LEDGER_CLOSE_S = 4
FLAG_INTERVAL = 256
LEDGERS_PER_DAY = 86400 // LEDGER_CLOSE_S  # 21600
DEFAULT_MAJORITY_HOLD_DAYS = 14
MIN_MAJORITY_HOLD_MINUTES = 15
PRE_FIX_NUM, PRE_FIX_DEN = 204, 256
POST_FIX_NUM, POST_FIX_DEN = 67, 100
VALIDATION_QUORUM_PCT = 0.67
ABS_MIN_QUORUM_PCT = 0.60
EXCLUSION_PCT = 0.67
EXCLUSION_RATE_LEDGERS = 10
REVOKE_SEQUENCE = 0xFFFFFFFF
START_LEDGER = 1000000


def _ceil_pct(n, pct):
    return int(math.ceil(n * pct))


class Amendment:
    """One amendment and its voting state (AmendmentTable.cpp)."""

    def __init__(self, name, vote_behavior, post_fix, has_code=True):
        self.name = name
        self.vote_behavior = vote_behavior  # DefaultYes | DefaultNo
        self.post_fix = post_fix
        self.has_code = has_code  # False -> effectively vetoed (line 648)
        self.support = 0  # validators voting up
        self.vetoed_by = set()  # validator ids that vetoed (vote down)
        self.majority_since_day = None
        self.enabled_day = None
        self.got_majority_count = 0
        self.lost_majority_count = 0
        self.enabled = False
        # Explicit up-voter set (scenario's set_support step). None
        # means "no explicit set": DefaultYes votes up by default,
        # DefaultNo votes down by default.
        self.up_voters = None

    def threshold(self, trusted_validations):
        if self.post_fix:
            return max(1, (trusted_validations * POST_FIX_NUM)
                       // POST_FIX_DEN)
        return max(1, (trusted_validations * PRE_FIX_NUM)
                   // PRE_FIX_DEN)

    def passes(self, trusted_validations):
        t = self.threshold(trusted_validations)
        if (not self.post_fix) or trusted_validations == 1:
            return self.support >= t
        return self.support > t


class Validator:
    """One validator: manifest state + availability (Manifest.h)."""

    def __init__(self, vid):
        self.vid = vid
        self.online = True
        self.has_new_binary = True  # False -> amendment-blocked risk
        self.manifest_seq = 1
        self.signing_key = "key-%s-1" % vid
        self.master_revoked = False
        self.unreliable = False  # negative-UNL marked
        self.excluded = False

    def rotate(self):
        self.manifest_seq += 1
        self.signing_key = "key-%s-%d" % (self.vid, self.manifest_seq)
        return self.manifest_seq

    def revoke(self):
        self.manifest_seq = REVOKE_SEQUENCE
        self.master_revoked = True
        return self.manifest_seq


class GovernanceNetwork:
    """The modeled network: validators, publishers, amendments, fees."""

    def __init__(self, config, log):
        self.log = log
        self.day = 0.0
        self.ledger_seq = START_LEDGER
        self.config = config
        n = config.get("validators", 35)
        self.validators = {("V%02d" % (i + 1)): Validator("V%02d" % (i + 1))
                           for i in range(n)}
        self.publishers = {}
        for p in config.get("publishers", ["P1", "P2", "P3"]):
            self.publishers[p] = {"available": True,
                                  "expiry_day": config.get(
                                      "publisher_expiry_day", 30.0)}
        self.post_fix = config.get("post_fix", True)
        self.majority_hold_days = config.get(
            "majority_hold_days", DEFAULT_MAJORITY_HOLD_DAYS)
        self.majority_hold_minutes = self.majority_hold_days * 24 * 60
        self.amendments = {}
        for a in config.get("amendments", []):
            self.amendments[a["name"]] = Amendment(
                a["name"], a.get("vote_behavior", "DefaultNo"),
                self.post_fix, a.get("has_code", True))
        self.fees = {"base_fee_drops": config.get("base_fee_drops", 10),
                     "account_reserve_drops": config.get(
                         "account_reserve_drops", 10 * 1000000),
                     "owner_reserve_drops": config.get(
                         "owner_reserve_drops", 2 * 1000000)}
        self.fee_targets = dict(self.fees)
        # fee_votes: field -> {value: count} from the latest fee_votes step
        self.fee_ballots = {}
        self.exclusion_queue = []
        self.exclusions = []
        self.counters = {
            "flag_ledgers": 0,
            "ledgers_validated": 0,
            "ledgers_missed": 0,
            "amendments_enabled": 0,
            "majority_restarts": 0,
            "fee_changes": 0,
            "exclusions_applied": 0,
            "manifests_rotated": 0,
            "manifests_revoked": 0,
            "validators_blocked": 0,
            "rollback_attempts": 0,
            "rollback_failures": 0,
            "replay_ledgers": 0,
            "quorum_disabled_flag_ledgers": 0,
        }
        self.events = []

    # -- logging ------------------------------------------------------
    def _log(self, msg):
        self.log.append("day %.4f ledger %d: %s"
                        % (self.day, self.ledger_seq, msg))

    # -- validator set -----------------------------------------------
    def trusted_validators(self):
        """Validators in the UNL: not revoked, not excluded."""
        return [v for v in self.validators.values()
                if not v.master_revoked and not v.excluded]

    def online_trusted(self):
        return [v for v in self.trusted_validators()
                if v.online and not self._is_blocked(v)]

    def _is_blocked(self, validator):
        """Amendment-blocked: a node running software without the code
        for an enabled amendment cannot determine ledger validity,
        submit/process transactions, participate in consensus, or vote
        on future amendments (xrpl.org 'Amendment Blocked Servers').
        Modelled as: old binary + at least one enabled amendment."""
        if validator.has_new_binary:
            return False
        return any(a.enabled for a in self.amendments.values())

    def blocked_validators(self):
        return [v for v in self.trusted_validators()
                if self._is_blocked(v)]

    def list_threshold(self):
        n = len(self.publishers)
        if n < 3:
            return 1
        return n // 2 + 1

    def validation_quorum(self):
        """ValidatorList::calculateQuorum. Returns None when quorum is
        disabled (too many publishers unavailable) — the chain halts
        rather than lowering the quorum (whitepaper 1.8)."""
        unl = self.trusted_validators()
        unl_size = len(unl)
        negative = sum(1 for v in unl if v.unreliable)
        effective = unl_size - negative
        unavailable = sum(1 for p in self.publishers.values()
                          if not p["available"])
        if self.publishers:
            lt = self.list_threshold()
            error_threshold = min(
                lt, len(self.publishers) - lt + 1)
            if unavailable >= error_threshold:
                return None
        q = max(_ceil_pct(effective, VALIDATION_QUORUM_PCT),
                _ceil_pct(unl_size, ABS_MIN_QUORUM_PCT))
        return q

    # -- amendment voting --------------------------------------------
    def amendment_threshold(self, name, trusted_validations):
        return self.amendments[name].threshold(trusted_validations)

    def _do_voting(self):
        """One flag ledger's AmendmentTableImpl::doVoting."""
        online = self.online_trusted()
        trusted_validations = len(online)
        for name, amd in self.amendments.items():
            if amd.enabled:
                continue
            if not amd.has_code:
                # Unknown amendments are effectively vetoed already
                # (AmendmentTable.cpp:648).
                continue
            # Support counts only validators actually voting up:
            # vetoed validators vote down, offline/blocked don't vote.
            up = sum(1 for v in online
                     if v.vid not in amd.vetoed_by
                     and self._validator_votes_up(v, amd))
            amd.support = up
            if amd.passes(trusted_validations):
                if amd.majority_since_day is None:
                    amd.majority_since_day = self.day
                    amd.got_majority_count += 1
                    self.events.append(
                        {"day": self.day, "event": "tfGotMajority",
                         "amendment": name, "support": up,
                         "trusted_validations": trusted_validations,
                         "threshold": amd.threshold(
                             trusted_validations)})
                    self._log("amendment %s tfGotMajority: support "
                              "%d/%d threshold %d"
                              % (name, up, trusted_validations,
                                 amd.threshold(trusted_validations)))
                elif (self.day - amd.majority_since_day
                        >= self.majority_hold_days):
                    amd.enabled = True
                    amd.enabled_day = self.day
                    self.counters["amendments_enabled"] += 1
                    self.events.append(
                        {"day": self.day, "event": "enabled",
                         "amendment": name, "support": up,
                         "trusted_validations": trusted_validations})
                    self._log("amendment %s ENABLED: support %d/%d "
                              "held %.4f days (hold %.4f)"
                              % (name, up, trusted_validations,
                                 self.day - amd.majority_since_day,
                                 self.majority_hold_days))
            else:
                if amd.majority_since_day is not None:
                    amd.lost_majority_count += 1
                    self.counters["majority_restarts"] += 1
                    held = self.day - amd.majority_since_day
                    self.events.append(
                        {"day": self.day, "event": "tfLostMajority",
                         "amendment": name, "support": up,
                         "trusted_validations": trusted_validations,
                         "held_days": held})
                    self._log("amendment %s tfLostMajority: support "
                              "%d/%d after holding %.4f days; "
                              "14-day clock restarts"
                              % (name, up, trusted_validations, held))
                    amd.majority_since_day = None

    def _validator_votes_up(self, validator, amd):
        """Vote behaviour: DefaultYes votes up unless vetoed;
        DefaultNo votes up only if explicitly configured (the
        scenario's support set)."""
        if amd.up_voters is not None:
            return validator.vid in amd.up_voters
        if amd.vote_behavior == "DefaultYes":
            return True
        return False

    # -- fee voting ---------------------------------------------------
    def _fee_vote(self):
        """One flag ledger's FeeVoteImpl::doVoting. Only trusted
        validators vote; VotableValue takes the most-voted value
        between current and target, inclusive; ties keep current."""
        online = self.online_trusted()
        for field in ("base_fee_drops", "account_reserve_drops",
                      "owner_reserve_drops"):
            votes = self.fee_ballots.get(field, {})
            if not votes:
                continue
            current = self.fees[field]
            target = self.fee_targets[field]
            lo, hi = min(current, target), max(current, target)
            counts = {}
            for value, count in votes.items():
                if lo <= value <= hi:
                    counts[value] = counts.get(value, 0) + count
            # Validators that did not submit a fee field count as
            # noVote (current); they are not in `votes`.
            if not counts:
                continue
            best = max(counts.values())
            winners = [v for v, c in counts.items() if c == best]
            chosen = current if current in winners else sorted(winners)[0]
            if chosen != current:
                self.fees[field] = chosen
                self.counters["fee_changes"] += 1
                self.events.append(
                    {"day": self.day, "event": "fee_change",
                     "field": field, "from": current, "to": chosen,
                     "votes": counts})
                self._log("fee vote %s: %d -> %d (votes %s, "
                          "trusted online %d)"
                          % (field, current, chosen, counts,
                             len(online)))
            # No log line when the fee stays: this runs at every flag
            # ledger and the outcome is recorded in the rows.

    # -- time advance -------------------------------------------------
    def _flag_ledgers_in(self, days):
        """Flag ledgers (every 256 ledgers) inside a span of days."""
        ledgers = int(days * LEDGERS_PER_DAY)
        start = self.ledger_seq
        end = start + ledgers
        first_flag = ((start + FLAG_INTERVAL - 1)
                      // FLAG_INTERVAL) * FLAG_INTERVAL
        if first_flag == 0:
            first_flag = FLAG_INTERVAL
        count = 0
        if first_flag < end:
            count = 1 + (end - 1 - first_flag) // FLAG_INTERVAL
        return ledgers, count

    def advance(self, days):
        """Advance the network by `days`, evaluating one flag ledger
        per 256 ledgers and validating (or missing) every ledger."""
        ledgers, flags = self._flag_ledgers_in(days)
        quorum = self.validation_quorum()
        online = len(self.online_trusted())
        if quorum is None:
            self.counters["ledgers_missed"] += ledgers
            self.counters["quorum_disabled_flag_ledgers"] += flags
            self._log("advance %.4f days (%d ledgers, %d flag "
                      "ledgers): quorum DISABLED (publishers "
                      "unavailable) — chain halts, %d ledgers missed"
                      % (days, ledgers, flags, ledgers))
        elif online >= quorum:
            self.counters["ledgers_validated"] += ledgers
            self._log("advance %.4f days (%d ledgers, %d flag "
                      "ledgers): quorum %d, online %d — all validated"
                      % (days, ledgers, flags, quorum, online))
        else:
            self.counters["ledgers_missed"] += ledgers
            self._log("advance %.4f days (%d ledgers, %d flag "
                      "ledgers): quorum %d, online %d — below quorum, "
                      "%d ledgers missed (chain halts)"
                      % (days, ledgers, flags, quorum, online,
                         ledgers))
        # Evaluate each flag ledger in order (same state, so the
        # outcome repeats; evaluate once per flag ledger for the
        # count, and run the voting logic once per distinct day
        # boundary to keep the log readable).
        for _ in range(flags):
            self.counters["flag_ledgers"] += 1
            self.ledger_seq += FLAG_INTERVAL
            self.day += FLAG_INTERVAL * LEDGER_CLOSE_S / 86400.0
            self._do_voting()
            self._fee_vote()
            self._exclusion_step()
        # Remainder ledgers to reach the exact span.
        remainder = ledgers - flags * FLAG_INTERVAL
        self.ledger_seq += remainder
        self.day += remainder * LEDGER_CLOSE_S / 86400.0
        # Correct floating drift: the span must be exact.
        return {"ledgers": ledgers, "flag_ledgers": flags,
                "quorum": quorum, "online": online}

    def _exclusion_step(self):
        """One exclusion change per 10 ledgers while agreement holds
        (docs/Exclusions.md:41, 191). The step is evaluated per flag
        ledger; the queue drains at the documented rate."""
        if not self.exclusion_queue:
            return
        # 256 ledgers per flag ledger / 10 ledgers per change.
        for _ in range(FLAG_INTERVAL // EXCLUSION_RATE_LEDGERS):
            if not self.exclusion_queue:
                return
            account = self.exclusion_queue.pop(0)
            self.exclusions.append(account)
            self.counters["exclusions_applied"] += 1
            self._log("exclusion applied: %s (1 per 10 ledgers)"
                      % account)

    # -- scenario operations -----------------------------------------
    def set_support(self, amendment, up_voters):
        amd = self.amendments[amendment]
        amd.up_voters = set(up_voters)
        self._log("amendment %s: up-voters set to %d validators"
                  % (amendment, len(up_voters)))

    def veto(self, amendment, validators):
        amd = self.amendments[amendment]
        for v in validators:
            amd.vetoed_by.add(v)
        self._log("amendment %s: vetoed by %s (vote persisted down)"
                  % (amendment, ",".join(validators)))

    def unveto(self, amendment, validators):
        amd = self.amendments[amendment]
        for v in validators:
            amd.vetoed_by.discard(v)
        self._log("amendment %s: un-vetoed by %s"
                  % (amendment, ",".join(validators)))

    def set_online(self, validators, online):
        for v in validators:
            self.validators[v].online = online
        self._log("validators %s -> %s"
                  % (",".join(validators),
                     "online" if online else "offline"))

    def set_binary(self, validators, has_new_binary):
        for v in validators:
            self.validators[v].has_new_binary = has_new_binary
        self._log("validators %s binary -> %s"
                  % (",".join(validators),
                     "new" if has_new_binary else "old (no code for "
                     "new amendments)"))

    def rotate_manifest(self, validator):
        seq = self.validators[validator].rotate()
        self.counters["manifests_rotated"] += 1
        self._log("validator %s manifest rotated: new ephemeral key, "
                  "sequence %d" % (validator, seq))
        return seq

    def revoke_manifest(self, validator):
        seq = self.validators[validator].revoke()
        self.counters["manifests_revoked"] += 1
        self._log("validator %s master key REVOKED: manifest sequence "
                  "0xFFFFFFFF; validator leaves the UNL" % validator)
        return seq

    def set_publisher(self, publisher, available):
        self.publishers[publisher]["available"] = available
        self._log("publisher %s -> %s"
                  % (publisher,
                     "available" if available else "unavailable"))

    def mark_unreliable(self, validators):
        for v in validators:
            self.validators[v].unreliable = True
        self._log("validators %s marked unreliable (negative UNL)"
                  % ",".join(validators))

    def fee_votes(self, field, distribution):
        # JSON object keys arrive as strings; fee values are ints.
        self.fee_ballots[field] = {int(k): v for k, v in
                                   distribution.items()}
        self._log("fee votes %s: %s" % (field, distribution))

    def exclusion_vote(self, account, agreeing):
        n_trusted = len(self.trusted_validators())
        needed = _ceil_pct(n_trusted, EXCLUSION_PCT)
        if agreeing >= needed:
            self.exclusion_queue.append(account)
            self._log("exclusion vote %s: %d/%d agree (>= %d, 67%%) "
                      "— queued" % (account, agreeing, n_trusted,
                                    needed))
            return True
        self._log("exclusion vote %s: %d/%d agree (< %d, 67%%) — "
                  "rejected" % (account, agreeing, n_trusted, needed))
        return False

    def majority_time_override(self, minutes):
        if minutes < MIN_MAJORITY_HOLD_MINUTES:
            raise ValueError("majority hold below the 15-minute "
                             "minimum (Config.cpp:895)")
        self.majority_hold_days = minutes / 1440.0
        self.majority_hold_minutes = minutes
        self._log("AMENDMENT_MAJORITY_TIME overridden to %d minutes "
                  "(was 14 days)" % minutes)

    def binary_upgrade(self, validators):
        """Sequential validator rollout (DeploymentWorkflows.md:85:
        max-parallel 1). Upgrading a validator restarts it with the
        new binary (code for pending amendments)."""
        for v in validators:
            self.validators[v].has_new_binary = True
        self._log("binary upgrade: %d validators upgraded "
                  "sequentially (max-parallel 1): %s"
                  % (len(validators), ",".join(validators)))

    def rollback_attempt(self, amendment):
        """Try to roll back an enabled amendment. There is no
        in-protocol path: disabling a passed amendment requires a new
        amendment (xrpl.org Amendments)."""
        self.counters["rollback_attempts"] += 1
        amd = self.amendments.get(amendment)
        if amd is not None and amd.enabled:
            self.counters["rollback_failures"] += 1
            self._log("rollback attempt on %s: FAILED — no "
                      "in-protocol rollback path; disabling a passed "
                      "amendment requires a new amendment"
                      % amendment)
            return False
        self._log("rollback attempt on %s: nothing to roll back "
                  "(not enabled)" % amendment)
        return False

    def ledger_replay(self, ledgers):
        """Per-node ledger replay (docs/0010-ledger-replay). Re-executes
        ledgers on one node; it does not un-enable amendments and does
        not rewind network state."""
        self.counters["replay_ledgers"] += ledgers
        self._log("ledger replay: %d ledgers re-executed on this node "
                  "only; enabled amendments unchanged" % ledgers)
        return ledgers

    def final_state(self):
        q = self.validation_quorum()
        return {
            "day": round(self.day, 4),
            "ledger_seq": self.ledger_seq,
            "unl_size": len(self.trusted_validators()),
            "online_trusted": len(self.online_trusted()),
            "validation_quorum": q,
            "blocked_validators": [v.vid for v in
                                   self.blocked_validators()],
            "fees": dict(self.fees),
            "exclusions": list(self.exclusions),
            "amendments": {
                name: {
                    "enabled": a.enabled,
                    "enabled_day": (round(a.enabled_day, 4)
                                    if a.enabled_day is not None
                                    else None),
                    "support": a.support,
                    "majority_since_day": (
                        round(a.majority_since_day, 4)
                        if a.majority_since_day is not None else None),
                    "got_majority_count": a.got_majority_count,
                    "lost_majority_count": a.lost_majority_count,
                    "vetoed_by": sorted(a.vetoed_by),
                    "has_code": a.has_code,
                } for name, a in self.amendments.items()},
            "counters": dict(self.counters),
        }
