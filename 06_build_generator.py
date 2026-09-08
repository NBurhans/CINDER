#!/usr/bin/env python3
"""CINDER Phase 4 — build generation.

Builds come from each species-form's OWN profile. Move slots fill from the pool
available AT THAT CHECKPOINT, never the lifetime pool. Four tracks, assigned by
the profile rather than chosen. Every pruning rule applied is recorded.
"""
import json, csv, collections, os

WORK, OUT = "/home/claude/work", "/mnt/user-data/outputs/cinder"
d = json.load(open(f"{WORK}/data.json"))
ITEMS = json.load(open(f"{WORK}/item_catalog.json"))
SP = d["species"]; MV = {int(k): v for k, v in d["moves"].items()}
TMs = {int(k): int(v) for k, v in d["tmMoves"].items()}
TUs = {int(k): int(v) for k, v in d["tutorMoves"].items()}
SPLIT = {0: "Physical", 1: "Special", 2: "Status"}
tyname = {int(k): v["name"] for k, v in d["types"].items()}
caps = sorted(((v["ID"], k, v["cap"][0]) for k, v in d["caps"].items()))

log = []
def L(c, s, t): log.append(dict(check=c, severity=s, detail=t))

# ---- the support-track utility whitelist. Published so it can be argued with.
UTIL = {
 # hazards and removal
 "Stealth Rock","Spikes","Toxic Spikes","Sticky Web","Rapid Spin","Defog","Court Change",
 # recovery and support
 "Recover","Roost","Soft-Boiled","Moonlight","Morning Sun","Synthesis","Slack Off","Milk Drink",
 "Shore Up","Wish","Heal Bell","Aromatherapy","Life Dew","Jungle Healing","Lunar Blessing",
 # status
 "Will-O-Wisp","Thunder Wave","Toxic","Spore","Sleep Powder","Hypnosis","Yawn","Glare",
 "Nuzzle","Stun Spore","Poison Powder","Leech Seed",
 # turn and momentum denial
 "Taunt","Encore","Disable","Roar","Whirlwind","Dragon Tail","Circle Throw","Haze","Clear Smog",
 "Perish Song","Destiny Bond","Trick","Switcheroo","Parting Shot","Memento","Baton Pass",
 "Teleport","Substitute","Protect","Detect","Spiky Shield","King's Shield","Burning Bulwark",
 # field control
 "Light Screen","Reflect","Aurora Veil","Trick Room","Tailwind","Safeguard","Mist",
 "Rain Dance","Sunny Day","Sandstorm","Snowscape","Electric Terrain","Grassy Terrain",
 "Misty Terrain","Psychic Terrain",
}
# ---- setup moves and what they boost. A setup move is not "utility" — it is the
# centre of a build, so it gets its own variant rather than a slot in the support pool.
SETUP = {
 "Swords Dance":{"atk":2}, "Nasty Plot":{"spa":2}, "Dragon Dance":{"atk":1,"spe":1},
 "Calm Mind":{"spa":1,"spd":1}, "Bulk Up":{"atk":1,"def":1},
 "Quiver Dance":{"spa":1,"spd":1,"spe":1}, "Shell Smash":{"atk":2,"spa":2,"spe":2,"def":-1,"spd":-1},
 "Agility":{"spe":2}, "Rock Polish":{"spe":2}, "Autotomize":{"spe":2},
 "Iron Defense":{"def":2}, "Amnesia":{"spd":2}, "Acid Armor":{"def":2}, "Barrier":{"def":2},
 "Work Up":{"atk":1,"spa":1}, "Growth":{"atk":1,"spa":1}, "Hone Claws":{"atk":1},
 "Coil":{"atk":1,"def":1}, "Curse":{"atk":1,"def":1,"spe":-1}, "Shift Gear":{"atk":1,"spe":2},
 "Tail Glow":{"spa":3}, "Belly Drum":{"atk":6}, "Victory Dance":{"atk":1,"def":1,"spe":1},
 "No Retreat":{"atk":1,"def":1,"spa":1,"spd":1,"spe":1},
 "Clangorous Soul":{"atk":1,"def":1,"spa":1,"spd":1,"spe":1},
 "Dragon Dance ":{"atk":1,"spe":1},
}
STAT_FOR = {"physical":"atk", "special":"spa", "mixed":"atk"}
L("B0a_setup_vocab", "INFO",
  f"{len(SETUP)} setup moves recognised with the stats each boosts. Setup is deliberately NOT in "
  f"the support whitelist: a setup move is the centre of a build, not a filler slot, so it "
  f"generates its own variant that is then measured against the non-setup build.")

L("B0_utility_whitelist", "INFO",
  f"support track gated on an explicit whitelist of {len(UTIL)} status moves that change a fight. "
  f"Growl and Tail Whip are status moves and are deliberately excluded.")

# ---- availability gates from Phase 2
world = list(csv.DictReader(open(f"{OUT}/02_world.tsv", encoding="utf-8"), delimiter="\t"))
item_gate, item_copies, mart = {}, collections.Counter(), set()
tm_gate, tutor_gate = {}, {}
for r in world:
    g = int(r["earliest_gate"])
    if r["entity_type"].startswith(("item_", "vendor_")):
        n = r["entity_name"]
        item_gate[n] = min(item_gate.get(n, 99), g)
        if r["entity_type"] == "vendor_stock": mart.add(n)
        else: item_copies[n] += 1
        if r["tm_number"] != "NA" and r["resolved_move"] != "UNK":
            tm_gate[r["resolved_move"]] = min(tm_gate.get(r["resolved_move"], 99), g)
    if r["entity_type"] == "tutor" and r["resolved_move"] != "UNK":
        tutor_gate[r["resolved_move"]] = min(tutor_gate.get(r["resolved_move"], 99), g)
fuchsia = [int(r["earliest_gate"]) for r in world
           if r["entity_type"] == "tutor" and r["location"].startswith("Fuchsia City")]
egg_gate = min(fuchsia) if fuchsia else 99
L("B1a_egg_move_tutor", "INFO",
  f"the egg-move tutor teaches no fixed move list, so it is absent from the `tutors` array. The "
  f"documentation places it in Fuchsia City, free after its challenge; Fuchsia's own tutor entry "
  f"sits at gate {egg_gate}, so egg moves are gated there. Gate is Asserted, the movepool itself "
  f"is Measured.")
L("B1_pool_gates", "INFO",
  f"move-pool gates from Phase 2: {len(tm_gate)} TM moves, {len(tutor_gate)} tutor moves, "
  f"{len(item_gate)} placed items. Egg-move tutor gate = "
  f"{egg_gate if egg_gate < 99 else 'NOT PLACED -> egg moves excluded from every pool'}.")

# ---- item preference, ranked PER TRACK (a single global ranking changes no orderings)
PREF = {
 "physical": ["choice_band","allout","type_boost","expert_belt","split_boost","choice_scarf",
              "sash","crit","punch_boost","multihit_boost","weakness_policy","resist_berry",
              "longevity","self_burn","charge","heal_berry"],
 "special":  ["choice_spec","allout","type_boost","expert_belt","split_boost","choice_scarf",
              "sash","crit","weakness_policy","resist_berry","longevity","charge","heal_berry"],
 "mixed":    ["allout","type_boost","expert_belt","choice_scarf","sash","crit","resist_berry",
              "longevity","charge","heal_berry"],
 "support":  ["longevity","eviolite","contact_punish","resist_berry","heal_berry","screen_ext",
              "weather_ext","terrain_seed","hazard_immune","ground_immune","assault_vest",
              "status_cure","type_boost"],
}
EV0 = None
EV = {"physical":"252 Atk / 252 Spe / 6 HP","special":"252 SpA / 252 Spe / 6 HP",
      "mixed":"252 Atk / 252 SpA / 6 Spe","support":"252 HP / 252 Def / 6 SpD","floor":"no EVs"}
NDMG = {"physical":3,"special":3,"mixed":4,"support":1}

by_tag = collections.defaultdict(list)
for v in ITEMS.values():
    if v["equippable"]: by_tag[v["tag"]].append(v)

def pick_items(track, cp, stab_types, nfe, k=3):
    """the top k items in the track's ranking that are obtainable by cp and usable by this
    form. These are CANDIDATES only — which one becomes the ceiling is decided by measuring
    them against the checkpoint's roster, not by their rank here."""
    out = []
    for tag in PREF[track]:
        for v in by_tag.get(tag, []):
            n = v["name"]
            g = item_gate.get(n)
            if g is None or g > cp: continue
            if tag == "type_boost" and v.get("boost_type") not in stab_types: continue
            if tag == "eviolite" and not nfe: continue
            reliable = (n in mart) or (item_copies[n] >= 3)
            out.append((n, tag, reliable, item_copies[n], (n in mart)))
            if len(out) >= k: return out
    return out or [("NONE", "none", True, 0, False)]

species = list(csv.DictReader(open(f"{OUT}/01_species.tsv", encoding="utf-8"), delimiter="\t"))
rows, no_track, prune = [], [], collections.Counter()

for cp, cpname, cap in caps:
    for s in species:
        if s["earliest_gate"] == "UNK" or int(s["earliest_gate"]) > cp:
            prune["not_yet_obtainable"] += 1; continue
        sid = s["internal_id"]
        raw = SP[sid]
        stab = {s["type_1"]} | ({s["type_2"]} if s["type_2"] != "NONE" else set())

        pool = {}
        for m, lv in raw.get("levelupMoves", []):
            if lv <= cap and m in MV: pool[MV[m]["name"]] = MV[m]
        for slot in raw.get("tmMoves", []):
            mid = TMs.get(slot, 0)
            if mid and mid in MV and tm_gate.get(MV[mid]["name"], 99) <= cp: pool[MV[mid]["name"]] = MV[mid]
        for slot in raw.get("tutorMoves", []):
            mid = TUs.get(slot, 0)
            if mid and mid in MV and tutor_gate.get(MV[mid]["name"], 99) <= cp: pool[MV[mid]["name"]] = MV[mid]
        if egg_gate <= cp:
            for m in raw.get("eggMoves", []):
                if m in MV: pool[MV[m]["name"]] = MV[m]
        if not pool: prune["empty_pool_at_checkpoint"] += 1; continue

        atk, spa = int(s["atk"]), int(s["spa"])
        bestP = max([m["power"] for m in pool.values() if SPLIT[m["split"]] == "Physical"] or [0])
        bestS = max([m["power"] for m in pool.values() if SPLIT[m["split"]] == "Special"] or [0])
        tracks, why = [], ""
        if atk >= 1.15*spa and bestP >= 60: tracks, why = ["physical"], f"atk {atk} >= 1.15*spa {spa}; bestP {bestP}"
        elif spa >= 1.15*atk and bestS >= 60: tracks, why = ["special"], f"spa {spa} >= 1.15*atk {atk}; bestS {bestS}"
        elif bestP >= 60 and bestS >= 60 and spa and 0.85 <= atk/spa <= 1.176:
            tracks, why = ["physical","special","mixed"], f"atk {atk} / spa {spa} within 15%; both pools >= 60 BP"
        else: why = f"no attacking track (bestP {bestP}, bestS {bestS}, max stat {max(atk,spa)})"
        util = [m for m in pool.values() if SPLIT[m["split"]] == "Status" and m["name"] in UTIL]
        if util and (max(atk,spa) < 80 or (bestP < 60 and bestS < 60)): tracks.append("support")
        if not tracks:
            no_track.append((cp, s["form_key"], bestP, bestS, max(atk,spa))); prune["no_track"] += 1; continue

        nfe = s["evolves_into"] != "NONE"
        tyof = {m["name"]: m["type"] for m in pool.values()}
        def eff_power(m):
            return m["power"] * (1.5 if tyname.get(m["type"]) in stab else 1.0)
        def pick(cat, n):
            """greedy: highest STAB-weighted power first, then prefer a new attacking type
            so the slots buy coverage rather than three flavours of the same thing"""
            cands = sorted([m for m in pool.values() if SPLIT[m["split"]] == cat and m["power"] > 0],
                           key=lambda m: -eff_power(m))
            out, seen = [], set()
            for m in cands:
                if len(out) >= n: break
                if m["type"] in seen and len(cands) > n: continue
                out.append(m); seen.add(m["type"])
            for m in cands:                      # backfill if coverage filtering starved it
                if len(out) >= n: break
                if m not in out: out.append(m)
            return out
        for tr in tracks:
            if tr == "physical":  dmg = pick("Physical", 3)
            elif tr == "special": dmg = pick("Special", 3)
            elif tr == "mixed":   dmg = pick("Physical", 2) + pick("Special", 2)
            else:                 dmg = pick("Physical" if atk >= spa else "Special", 1)
            used = {m["name"] for m in dmg}
            sup = [m for m in sorted(util, key=lambda m: -eff_power(m) if m["power"] else 0)
                   if m["name"] not in used][:4-len(dmg)]
            moves = [m["name"] for m in dmg] + [m["name"] for m in sup]
            cands = pick_items(tr, cp, stab, nfe, 3)
            item, tag, reliable, copies, purch = cands[0]
            variants = [(tr, moves, "NONE")]
            if tr in STAT_FOR:
                want = STAT_FOR[tr]
                usable = [m for m in pool.values() if m["name"] in SETUP
                          and (SETUP[m["name"]].get(want, 0) > 0 or SETUP[m["name"]].get("spe", 0) > 0)]
                if usable and len(dmg) >= 2:
                    # rank by how much of what this build needs the move actually gives
                    su = max(usable, key=lambda m: SETUP[m["name"]].get(want,0)*2 + SETUP[m["name"]].get("spe",0))
                    keep = [m["name"] for m in dmg[:-1]]            # drop the weakest damaging move
                    extra = [m["name"] for m in sup][:max(0, 3-len(keep))]
                    variants.append((tr + "_setup", keep + [su["name"]] + extra, su["name"]))
            for vtrack, vmoves, vsetup in variants:
              rows.append(dict(checkpoint=cp, checkpoint_name=cpname, level=cap,
                             internal_id=sid, form_key=s["form_key"], track=vtrack,
                             setup_move=vsetup,
                             ev_spread=EV[tr], nature="Hardy", ability=s["ability_1"],
                             item=item, item_tag=tag, item_reliable="TRUE" if reliable else "FALSE",
                             item_copies=copies, item_purchasable="TRUE" if purch else "FALSE",
                             item_candidates="|".join(f"{c[0]}:{c[1]}:{'T' if c[2] else 'F'}" for c in cands),
                             moves=",".join(vmoves), n_moves=len(vmoves),
                             pool_size=len(pool), best_physical_bp=bestP, best_special_bp=bestS,
                             track_reason=why, anchor="ceiling",
                             confidence="Derived", notes="pool gated to this checkpoint"))
        # floor: zero investment, level-up moves only, no item
        lvl_only = sorted([MV[m] for m, lv in raw.get("levelupMoves", []) if lv <= cap and m in MV],
                          key=lambda m: -m["power"])[:4]
        rows.append(dict(checkpoint=cp, checkpoint_name=cpname, level=cap, internal_id=sid,
                         form_key=s["form_key"], track="floor", setup_move="NONE", ev_spread=EV["floor"],
                         nature="Hardy", ability=s["ability_1"], item="NONE", item_tag="none",
                         item_reliable="TRUE", item_copies=0, item_purchasable="FALSE",
                         moves=",".join(m["name"] for m in lvl_only), n_moves=len(lvl_only),
                         pool_size=len(pool), best_physical_bp=bestP, best_special_bp=bestS,
                         track_reason="zero-investment anchor", anchor="floor",
                         confidence="Derived", notes="level-up moves only, no item, no EVs"))

L("B2_pruning", "INFO", "pruning rules applied: " + "; ".join(f"{k}={v}" for k, v in prune.items()))
L("B3_no_track", "WARN",
  f"{len(no_track)} (species-form, checkpoint) pairs qualified for NO track and are a finding, not "
  f"a silent drop. Distinct forms affected: {len({x[1] for x in no_track})}. "
  f"Sample {no_track[:6]}")

with open(f"{OUT}/04a_builds.tsv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
    w.writeheader(); w.writerows(rows)
json.dump(log, open(f"{OUT}/INT_integrity_log_phase4a.json", "w"), indent=1)

print(f"wrote {len(rows)} builds")
tr = collections.Counter(r["track"] for r in rows)
for k, v in tr.most_common(): print(f"   {k:10s} {v}")
print()
for e in log: print(f"  [{e['severity']}] {e['check']}: {e['detail'][:170]}")
