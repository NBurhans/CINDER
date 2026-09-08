#!/usr/bin/env python3
"""CINDER Phase 4 — held-item catalogue.

Every item is classified from the hack's OWN name and description text, so a
hack-custom or rewritten item is classified on what this game says it does.
Tag assignment is Derived. Order matters: first rule that matches wins.
"""
import json, re, collections

d = json.load(open("/home/claude/work/data.json"))
IT = d["items"]

RULES = [
 ("choice_scarf",    r"^Choice Scarf$", None),
 ("choice_band",     r"^Choice Band$", None),
 ("choice_spec",     r"^Choice Specs$", None),
 ("eviolite",        r"^Eviolite$", None),
 ("allout",          r"^Life Orb$", None),
 ("assault_vest",    None, r"raises Sp\. Def but prevents"),
 ("expert_belt",     None, r"boosts the power of super effective"),
 ("longevity",       r"^(Leftovers|Black Sludge|Shell Bell|Berry Juice)$", None),
 ("resist_berry",    None, r"reduces damage taken from one super effective"),
 ("heal_berry",      None, r"(restore \d+% HP|heal any problem)"),
 ("pinch_berry",     None, r"(HP is low|in a pinch|when its HP)"),
 ("status_cure",     None, r"(cures?|heals?) (any )?(problem|status|paralysis|burn|poison|sleep|confusion)"),
 ("sash",            r"^(Focus Sash|Focus Band)$", None),
 ("contact_punish",  r"^(Rocky Helmet|Sticky Barb)$", None),
 ("weakness_policy", r"^Weakness Policy$", None),
 ("crit",            r"^(Scope Lens|Razor Claw)$", None),
 ("punch_boost",     r"^Punching Glove$", None),
 ("multihit_boost",  r"^Loaded Dice$", None),
 ("self_burn",       r"^Flame Orb$", None),
 ("self_poison",     r"^Toxic Orb$", None),
 ("quick_claw",      None, r"may be able to strike first"),
 ("charge",          r"^(Power Herb|Metronome|Throat Spray|White Herb|Mental Herb)$", None),
 ("hazard_immune",   r"^Heavy-Duty Boots$", None),
 ("ground_immune",   r"^Air Balloon$", None),
 ("screen_ext",      r"^Light Clay$", None),
 ("weather_ext",     r"^(Damp Rock|Heat Rock|Icy Rock|Smooth Rock)$", None),
 ("terrain_ext",     r"^Terrain Extender$", None),
 ("terrain_seed",    r"Seed$", None),
 ("split_boost",     None, r"slightly boosts the power of (physical|special)"),
 ("type_boost",      None, r"boosts (the power of|determination and) [A-Z][a-z]+-type"),
 ("species_locked",  None, r"held by (a |an |the )?(?!Pok)[A-Z]"),
 ("gem",             r"Gem$", None),
 ("mega_stone",      None, r"[Mm]ega ?[Ee]volv"),
 ("z_crystal",       r"ium Z$", None),
 ("plate",           r"Plate$", None),
 ("memory",          r"Memory$", None),
 ("drive",           r"Drive$", None),
 ("ev_gear",         r"^(Power Bracer|Power Belt|Power Lens|Power Band|Power Anklet|Power Weight|Macho Brace|Wide Lens|Zoom Lens|Bright Powder|Iron Ball|Ring Target|Safety Goggles|Protective Pads|Eject Button|Red Card|Absorb Bulb|Cell Battery|Snowball|Luminous Moss|Adrenaline Orb|Blunder Policy|Room Service|Utility Umbrella|Covert Cloak|Clear Amulet|Mirror Herb|Booster Energy|Shed Shell|Smoke Ball|Everstone|Destiny Knot|Cleanse Tag|Soothe Bell|Amulet Coin|Lucky Egg|Exp\. Share)$", None),
 ("evolution_item",  r"(Stone|Scale|Coat|Cable|Sweet|Chipped|Cracked|Peat|Auspicious|Malicious|Leader|Sachet|Ribbon|Upgrade|Dubious|Protector|Magmarizer|Electirizer|Reaper|Oval|King's Rock|Razor Fang)$", None),
 ("ball",            r"Ball$", None),
 ("tm",              r"^(TM|HM)\d+$", None),
 ("medicine",        None, r"(Restores|Heals|Revives|restores|Eliminates)"),
 ("vitamin",         r"^(HP Up|Protein|Iron|Calcium|Zinc|Carbos|PP Up|PP Max|Rare Candy|Ability Pill|Ability Capsule|Dream Patch)$", None),
 ("wing",            r"Wing$", None),
 ("sellable",        None, r"(sell|sold) (it |them )?(to|at|for)"),
]

EQUIPPABLE = {"choice_scarf","choice_band","choice_spec","eviolite","allout","assault_vest",
              "expert_belt","longevity","resist_berry","heal_berry","pinch_berry","status_cure",
              "sash","contact_punish","weakness_policy","crit","punch_boost","multihit_boost",
              "self_burn","self_poison","quick_claw","charge","hazard_immune","ground_immune",
              "screen_ext","weather_ext","terrain_ext","terrain_seed","species_locked",
              "split_boost","type_boost","gem","mega_stone","z_crystal","plate","memory",
              "drive","ev_gear"}

cat, tags = {}, collections.Counter()
for k, v in IT.items():
    nm, desc = v["name"], (v.get("description") or "")
    t = None
    for tag, npat, dpat in RULES:
        if npat and not re.search(npat, nm): continue
        if dpat and not re.search(dpat, desc, re.I): continue
        t = tag; break
    if t is None:
        t = "utility_misc" if re.search(r"held by a Pok", desc, re.I) else "unclassified"
    boost = None
    if t == "type_boost":
        m = re.search(r"([A-Z][a-z]+)-type", desc)
        boost = m.group(1) if m else None
    cat[int(k)] = dict(id=int(k), name=nm, tag=t, boost_type=boost,
                       equippable=t in EQUIPPABLE, description=desc)
    tags[t] += 1

json.dump(cat, open("/home/claude/work/item_catalog.json", "w"), indent=0)
print(f"classified {len(cat)} items into {len(tags)} tags; "
      f"{sum(1 for v in cat.values() if v['equippable'])} equippable")
for t, n in tags.most_common(16): print(f"   {t:16s} {n}")
print("\nspot checks:")
for nm in ("Charcoal","Occa Berry","Assault Vest","Expert Belt","Muscle Band","Thick Club",
           "Light Ball","Venusaurite","Sitrus Berry","Life Orb","Choice Scarf","Heavy-Duty Boots"):
    m = next((v for v in cat.values() if v["name"] == nm), None)
    lab = (m["tag"] + (f" ({m['boost_type']})" if m.get("boost_type") else "")) if m else "NOT FOUND"
    print(f"   {nm:18s} -> {lab}")
