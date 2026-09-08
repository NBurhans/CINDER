#!/usr/bin/env python3
"""CINDER Phase 3 — trainers, bosses, checkpoint graph. One row per (trainer, mode)."""
import json, csv, collections, os

WORK, OUT = "/home/claude/work", "/mnt/user-data/outputs/cinder"
d = json.load(open(f"{WORK}/data.json"))
SP, MV, IT, AB = d["species"], d["moves"], d["items"], d["abilities"]
T, CAPS, SCALED = d["trainers"], d["caps"], {int(k): v for k, v in d["scaledLevels"].items()}
tyname = {int(k): v["name"] for k, v in d["types"].items()}
matchup = {int(k): v["matchup"] for k, v in d["types"].items()}
EFF = {0: 1.0, 5: 0.5, 20: 2.0, 1: 0.0}
mv = {int(k): v for k, v in MV.items()}
it = {int(k): v["name"] for k, v in IT.items()}
ab = {int(k): (v["names"][0] if v.get("names") else "UNK") for k, v in AB.items()}
key = {int(k): v.get("key", v["name"]) for k, v in SP.items()}
nat = {int(k): v for k, v in d["natures"].items()}
cap_by_id = {v["ID"]: (k, v["cap"]) for k, v in CAPS.items()}

CANONICAL_MODE = "normal"      # target config: default mode
CAP_INDEX = 0                  # confirmed 18/18 against the published boss sheet

log = []
def L(c, s, t): log.append(dict(check=c, severity=s, detail=t))
def esc(x): return str(x).replace("\t", r"\t").replace("\n", r"\n").replace("|", r"\|")

L("T0_cap_resolution", "INFO",
  "caps carry a two-element array. cap[0] matches the level cap published in the official "
  "default-mode boss sheet on 18/18 gates and is used for every cap-relative resolution. "
  "cap[1] is unidentified; the dex tool's own filter code indexes cap by a difficulty key of "
  "normal|hardcore, which makes [normal, hardcore] the leading reading. Inferred, non-blocking "
  "for the canonical mode.")
L("T0b_type_chart", "INFO",
  "type matchup encoding 0=x1, 5=x0.5, 20=x2, 1=x0 reproduces 12/12 known relations. The array "
  "is 24 long against 18 types; the trailing six are mostly zero but NOT pure padding — Fighting "
  "carries a 5 at index 23. Unexplained, logged, and not read by anything downstream.")

abvals = sorted({p["ability"] for t in T.values() for m in ("normal","hardcore") for p in t[m]})
L("T0c_ability_slot", "WARN",
  f"roster `ability` takes values {abvals}. Three ability slots exist, so this reads as a 1-based "
  f"slot with 0 meaning unspecified, not an ability ID. Inferred — confirm before any ability-gated "
  f"role score in Phase 5.")

def resolve(level, capidx):
    if level in SCALED:
        return cap_by_id[capidx][1][CAP_INDEX] + SCALED[level], True
    return level, False

def eff(atk_t, def_types):
    m = 1.0
    for dt in def_types: m *= EFF[matchup[atk_t][dt]]
    return m

COLS = ["trainer_id","name","trainer_class","role","location","mode","cap_index","cap_name",
        "level_cap","is_level_scaled","boss_key","party_size","roster","roster_species",
        "max_level","min_level","offensive_types","mean_base_speed","fastest_member",
        "slowest_member","shared_weaknesses","team_resisted_by","strategy_notes",
        "source_record","confidence","notes"]

rows, dupnames, scaled_ct = [], collections.defaultdict(list), 0
unresolved_sp = unresolved_mv = unresolved_it = 0

for tid, t in sorted(T.items(), key=lambda kv: int(kv[0])):
    capidx = t["cap"]; capname, capval = cap_by_id[capidx]
    dupnames[t["name"]].append((capidx, t.get("areaName","UNK"), int(tid)))
    for mode in ("normal", "hardcore"):
        party = t[mode]
        if not party: continue
        slots, levels, types_off, spds, names, any_scaled = [], [], set(), [], [], False
        member_types = []
        for p in party:
            s = SP.get(str(p["species"]))
            if s is None: unresolved_sp += 1; continue
            lv, sc = resolve(p["level"], capidx)
            any_scaled |= sc
            levels.append(lv)
            st = s["stats"]; spds.append(st[3])          # internal order: Speed at index 3
            tt = [x for x in s["type"]]
            member_types.append(tt)
            names.append(key[p["species"]])
            mvn = []
            for m in p["moves"]:
                if m == 0: mvn.append("NONE"); continue
                mo = mv.get(m)
                if mo is None: unresolved_mv += 1; mvn.append(f"UNK{m}"); continue
                mvn.append(mo["name"])
                if mo["power"] and mo["power"] > 0: types_off.add(mo["type"])
            item = p.get("item")
            if item is not None and item not in it: unresolved_it += 1
            abn = ["ability_1","ability_2","ability_hidden"]
            aslot = max(0, p["ability"] - 1) if p["ability"] else 0
            aname = ab.get(s["abilities"][aslot][0], "UNK") if aslot < 3 else "UNK"
            ivs, evs = p["IVs"], p["EVs"]                # same internal order as stats
            conv = lambda a: [a[0], a[1], a[2], a[4], a[5], a[3]]   # -> HP Atk Def SpA SpD Spe
            slots.append(":".join([esc(key[p["species"]]), str(lv), str(p["level"]),
                                   esc(aname), esc(it.get(item, "NONE") if item is not None else "NONE"),
                                   esc(nat.get(p["nature"], "UNK")),
                                   "/".join(map(str, conv(ivs))), "/".join(map(str, conv(evs))),
                                   ",".join(esc(x) for x in mvn)]))
        if not slots: continue
        scaled_ct += any_scaled

        # derived team analysis
        weak = collections.Counter()
        for tt in member_types:
            for at in tyname:
                if eff(at, tt) > 1: weak[at] += 1
        shared = [tyname[a] for a, c in weak.items() if c >= max(2, len(member_types)/2)]
        resisted = [tyname[dt] for dt in tyname
                    if types_off and all(eff(at, [dt]) < 1 for at in types_off)]
        fast = names[spds.index(max(spds))]; slow = names[spds.index(min(spds))]

        note = (f"{len(names)} slots, levels {min(levels)}-{max(levels)}. "
                f"Offense covers {len(types_off)} types. "
                + (f"Shared weakness: {', '.join(shared)}. " if shared else "No weakness shared by half the team. ")
                + (f"A pure {resisted[0]} type resists everything it carries. " if resisted else "")
                + f"Speed spans {min(spds)}-{max(spds)} base, fastest {fast}, slowest {slow}."
                + (" LEVEL-SCALED: rescales to the player, excluded from scoring." if any_scaled else ""))

        rows.append({
          "trainer_id": int(tid), "name": esc(t["name"]),
          "trainer_class": t.get("class", "NA"),
          "role": "boss_candidate" if len(names) >= 4 else "route",
          "location": esc(t.get("areaName", "UNK")), "mode": mode,
          "cap_index": capidx, "cap_name": capname, "level_cap": capval[CAP_INDEX],
          "is_level_scaled": "TRUE" if any_scaled else "FALSE",
          "boss_key": f"{capidx}|{esc(t.get('areaName','UNK'))}|{esc(t['name'])}",
          "party_size": len(names), "roster": "|".join(slots),
          "roster_species": ",".join(esc(n) for n in names),
          "max_level": max(levels), "min_level": min(levels),
          "offensive_types": ",".join(tyname[x] for x in sorted(types_off)) or "NONE",
          "mean_base_speed": round(sum(spds)/len(spds), 1),
          "fastest_member": esc(fast), "slowest_member": esc(slow),
          "shared_weaknesses": ",".join(shared) or "NONE",
          "team_resisted_by": ",".join(resisted) or "NONE",
          "strategy_notes": esc(note),
          "source_record": f"data.js:trainers[{tid}].{mode}",
          "confidence": "Measured", "notes": "derived: team analysis; strategy_notes Inferred",
        })

dups = {k: v for k, v in dupnames.items() if len(v) > 1}
L("T3_duplicate_names", "WARN",
  f"{len(dups)} trainer names are shared by more than one trainer, covering "
  f"{sum(len(v) for v in dups.values())} records. Bosses are keyed on (cap, area, name). "
  f"Sample: {[(k, v) for k, v in list(dups.items())[:4]]}")
L("T2_scaled", "INFO",
  f"{scaled_ct} (trainer, mode) rows contain at least one cap-relative sentinel, resolved against "
  f"cap[0]. Raw sentinel retained per slot alongside the resolved level.")
L("T4_referential", "WARN" if (unresolved_sp or unresolved_mv or unresolved_it) else "INFO",
  f"unresolved roster references — species {unresolved_sp}, moves {unresolved_mv}, items {unresolved_it}")

diff = sum(1 for t in T.values() if t["normal"] != t["hardcore"])
L("T1_mode_split", "INFO",
  f"{diff} of {len(T)} trainers differ between modes. Both parsed and tagged; only "
  f"{CANONICAL_MODE} is scored.")

with open(f"{OUT}/03_trainers.tsv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS, delimiter="\t", lineterminator="\n")
    w.writeheader(); w.writerows(rows)

# ---- checkpoint graph
ck = []
for cid in sorted(cap_by_id):
    nm, cv = cap_by_id[cid]
    at = [r for r in rows if r["cap_index"] == cid and r["mode"] == CANONICAL_MODE]
    authored = [r for r in at if r["is_level_scaled"] == "FALSE" and r["party_size"] >= 4]
    ck.append(dict(checkpoint_index=cid, checkpoint_name=nm, level_cap=cv[CAP_INDEX],
                   cap_secondary=cv[1], trainers_total=len(at),
                   authored_boss_candidates=len(authored),
                   scored_roster_slots=sum(r["party_size"] for r in authored),
                   has_own_roster="TRUE" if authored else "FALSE",
                   source_record=f"data.js:caps[{nm}]", confidence="Measured"))
with open(f"{OUT}/03b_checkpoints.tsv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(ck[0]), delimiter="\t", lineterminator="\n")
    w.writeheader(); w.writerows(ck)

json.dump(log, open(f"{OUT}/INT_integrity_log_phase3.json", "w"), indent=1)
print(f"wrote {len(rows)} trainer-mode rows, {len(ck)} checkpoints")
for e in log: print(f"  [{e['severity']}] {e['check']}: {e['detail'][:150]}")
