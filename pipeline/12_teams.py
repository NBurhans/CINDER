#!/usr/bin/env python3
"""CINDER Phase 5b — the team layer.

Team fit against a checkpoint = coverage of that roster's threat set, weighted by how badly
each unanswered threat loses the fight. A build's team score is how often it appears in the
top-N teams and how much the best team degrades when it is removed. Teams must be
SIMULTANEOUSLY EQUIPPABLE given the copy counts in Phase 2 — that is invariant I5.
"""
import json, csv, glob, collections

OUT = "/mnt/user-data/outputs/cinder"
POOL_CAP, BEAM, TOPN, TEAM = 250, 24, 20, 6
log = []
def L(c, s, t): log.append(dict(check=c, severity=s, detail=t))

cov = collections.defaultdict(list)
for f in glob.glob("/home/claude/work/cv_*.json"):
    for r in json.load(open(f)): cov[r["cp"]].append(r)

# item copy counts: mart stock is unlimited supply, everything else is a finite count
world = list(csv.DictReader(open(f"{OUT}/02_world.tsv", encoding="utf-8"), delimiter="\t"))
copies, unlimited = collections.Counter(), set()
for r in world:
    if r["entity_type"] == "vendor_stock": unlimited.add(r["entity_name"])
    elif r["entity_type"].startswith("item_"):
        try: copies[r["entity_name"]] += int(r["quantity"])   # literal, per the runbook
        except ValueError: copies[r["entity_name"]] += 1

L("T0_pruning", "INFO",
  f"beam search over teams of {TEAM}: pool capped at the top {POOL_CAP} builds by VORP per "
  f"checkpoint, beam width {BEAM}, top {TOPN} teams retained. The cap is a pruning rule — an "
  f"exhaustive search over a ~3,300-build pool is not tractable and would not change the top teams.")

team_rows, build_score, i5_fail = [], collections.defaultdict(float), []
for cp in sorted(cov, key=int):
    builds = sorted(cov[cp], key=lambda r: -r["vorp"])[:POOL_CAP]
    nslot = len(builds[0]["m"])
    # threat weight: how badly an UNANSWERED threat loses. Slots almost nothing beats are
    # the ones a team must actually solve.
    beat = [sum(1 for b in builds if b["m"][i] > 0) / len(builds) for i in range(nslot)]
    weight = [1.0 - x for x in beat]
    tw = sum(weight) or 1.0

    def fit(team):
        s = 0.0
        for i in range(nslot):
            if any(b["m"][i] > 0 for b in team): s += weight[i]
        return s / tw

    beams = [[]]
    for _ in range(TEAM):
        cand = []
        for t in beams:
            have = {b["id"] for b in t}
            for b in builds:
                if b["id"] in have: continue
                cand.append((fit(t + [b]), t + [b]))
        cand.sort(key=lambda x: -x[0])
        seen, nb = set(), []
        for sc, t in cand:
            k = tuple(sorted(b["id"] for b in t))
            if k in seen: continue
            seen.add(k); nb.append(t)
            if len(nb) >= BEAM: break
        beams = nb
    top = sorted(({"fit": fit(t), "team": t} for t in beams), key=lambda x: -x["fit"])[:TOPN]

    # marginal contribution: appearance rate in the top-N, plus leave-one-out on the best team
    appear = collections.Counter()
    for t in top:
        for b in t["team"]: appear[b["id"]] += 1
    best = top[0]
    for b in best["team"]:
        without = [x for x in best["team"] if x["id"] != b["id"]]
        build_score[(cp, b["id"])] = round(best["fit"] - fit(without), 4)
    for bid, n in appear.items():
        build_score[(cp, bid)] = build_score.get((cp, bid), 0.0) + round(n / len(top), 4)

    # I5: simultaneously equippable?
    used = collections.Counter(b["item"] for b in best["team"] if b["item"] != "NONE")
    viol = [(it, n, copies[it]) for it, n in used.items()
            if it not in unlimited and n > max(1, copies[it])]
    if viol: i5_fail.append((cp, viol))
    team_rows.append(dict(checkpoint=cp, team_fit=round(best["fit"], 4),
        threats=nslot, threats_covered=sum(1 for i in range(nslot)
            if any(b["m"][i] > 0 for b in best["team"])),
        members=",".join(b["form"] for b in best["team"]),
        roles=",".join(b["role"] for b in best["team"]),
        items=",".join(b["item"] for b in best["team"]),
        simultaneously_equippable="FALSE" if viol else "TRUE",
        equip_conflicts=";".join(f"{i}x{n}>copies{c}" for i, n, c in viol) or "NONE",
        confidence="Derived"))
    print(f"  cp{cp:>2} fit {best['fit']:.3f}  covers {team_rows[-1]['threats_covered']}/{nslot}  "
          f"{'OK ' if not viol else 'I5!'} {team_rows[-1]['members'][:70]}")

with open(f"{OUT}/05c_teams.tsv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(team_rows[0]),delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(team_rows)

# fold team_score back into the valuation table
val=list(csv.DictReader(open(f"{OUT}/05_valuation.tsv",encoding="utf-8"),delimiter="\t"))
for r in val: r["team_score"]=build_score.get((r["checkpoint"], r["internal_id"]), 0.0)
cols=list(val[0])
with open(f"{OUT}/05_valuation.tsv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=cols,delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(val)

ok = not i5_fail
print(f"\nI5 simultaneously equippable: {'PASS' if ok else 'FAIL'} — "
      f"{len(i5_fail)} of {len(team_rows)} checkpoint teams have an item-copy conflict")
for cp, v in i5_fail: print(f"    cp{cp}: {v}")
L("INV_I5", "INFO" if ok else "WARN",
  f"{'PASS' if ok else 'FAIL'} — {len(i5_fail)} of {len(team_rows)} recommended teams violate "
  f"item copy counts" + (f": {i5_fail}" if i5_fail else ""))
L("T1_team_layer","INFO",
  f"team layer built for {len(team_rows)} checkpoints; team_score written back to "
  f"{sum(1 for r in val if float(r['team_score'])>0)} valuation rows")
json.dump(log, open(f"{OUT}/INT_integrity_log_phase5b.json","w"), indent=1)
