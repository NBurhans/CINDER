// CINDER Phase 4 — measured item selection and the 1v1 matrix.
//
// Items are NOT chosen by rank. The generator proposes up to three candidates per
// (form, checkpoint, track); every one is run against that checkpoint's authored
// roster and the ceiling is whichever actually performs best. Item dependence then
// falls out as a measurement: best item minus best reliably-obtainable item.
//
// Priority MOVES ORDER TURNS here. SABLE scored priority without simulating it.
const fs = require('fs');
const {calculate, Pokemon, Move, Field} = require('/home/claude/calc/calc/dist/adaptable.js');
const L = require('/home/claude/work/data_layer.js');
const gen = L.gen;
const CAT = require('/home/claude/work/item_catalog.json');
const tagOf = {}; for (const k in CAT) tagOf[CAT[k].name] = CAT[k].tag;

const OUT = '/mnt/user-data/outputs/cinder';
const tsv = p => {
  const l = fs.readFileSync(p, 'utf8').split('\n').filter(Boolean);
  const h = l[0].split('\t');
  return l.slice(1).map(r => { const f = r.split('\t'); const o = {}; h.forEach((c, i) => o[c] = f[i]); return o; });
};

const EVOF = s => {                       // "252 Atk / 252 Spe / 6 HP" -> {atk:252,...}
  const m = {hp:0, atk:0, def:0, spa:0, spd:0, spe:0};
  const K = {HP:'hp', Atk:'atk', Def:'def', SpA:'spa', SpD:'spd', Spe:'spe'};
  for (const p of s.split('/')) {
    const t = p.trim().split(/\s+/);
    if (t.length === 2 && K[t[1]]) m[K[t[1]]] = +t[0];
  }
  return m;
};
const HEAL_RECOVERY = 0.25, HEAL_REGEN = 0.11, HEAL_LEFT = 0.0625;
const RECOVERY = new Set(['Recover','Roost','Soft-Boiled','Moonlight','Morning Sun','Synthesis',
  'Slack Off','Milk Drink','Shore Up','Wish','Life Dew','Jungle Healing','Lunar Blessing']);

const ANCHOR = process.env.ANCHOR || 'ceiling';
const builds = tsv(`${OUT}/04a_builds.tsv`).filter(b => b.anchor === ANCHOR);
const trainers = tsv(`${OUT}/03_trainers.tsv`).filter(t =>
  t.mode === 'normal' && t.is_level_scaled === 'FALSE' && +t.party_size >= 4);

// roster slots per checkpoint
const roster = {};
for (const t of trainers) {
  (roster[t.cap_index] ||= []).push(...t.roster.split('|').map(s => {
    const f = s.split(':');
    return {species: f[0], level: +f[1], ability: f[3], item: f[4], nature: f[5],
            ivs: f[6].split('/').map(Number), evs: f[7].split('/').map(Number),
            moves: (f[8] || '').split(','), trainer: t.trainer_id};
  }));
}

const mk = (name, lvl, item, ability, nature, evs, ivs) => {
  try {
    return new Pokemon(gen, name, {level: lvl, item: item && item !== 'NONE' ? item : undefined,
      ability: ability && ability !== 'NONE' ? ability : undefined,
      nature: nature || 'Hardy', evs, ivs});
  } catch (e) { return null; }
};
const S = ['hp','atk','def','spa','spd','spe'];
const arr2 = a => ({hp:a[0], atk:a[1], def:a[2], spa:a[3], spd:a[4], spe:a[5]});

// returns every damaging move's fraction, so the Choice lock can be scored on ONE move
const dmgAll = (att, def, moves) => {
  const per = {};
  let best = 0, bestPri = -7, bestName = null;
  for (const mn of moves) {
    if (!mn || mn === 'NONE' || per[mn] !== undefined) continue;
    const md = L.moveById[mn.toLowerCase().replace(/[^a-z0-9]+/g, '')];
    if (!md || !md.basePower) continue;
    let r;
    try { r = calculate(gen, att, def, new Move(gen, md.name), new Field()); } catch (e) { continue; }
    const d = r.damage;
    const avg = Array.isArray(d) ? (d[0] + d[d.length-1]) / 2 : d;
    const frac = avg / def.maxHP();
    per[md.name] = {frac, priority: md.priority || 0};
    if (frac > best) { best = frac; bestPri = md.priority || 0; bestName = md.name; }
  }
  return {frac: best, priority: bestPri, move: bestName, per};
};
const CHOICE = new Set(['Choice Band', 'Choice Specs', 'Choice Scarf']);
const SETUP = {
 'Swords Dance':{atk:2},'Nasty Plot':{spa:2},'Dragon Dance':{atk:1,spe:1},
 'Calm Mind':{spa:1,spd:1},'Bulk Up':{atk:1,def:1},'Quiver Dance':{spa:1,spd:1,spe:1},
 'Shell Smash':{atk:2,spa:2,spe:2,def:-1,spd:-1},'Agility':{spe:2},'Rock Polish':{spe:2},
 'Autotomize':{spe:2},'Iron Defense':{def:2},'Amnesia':{spd:2},'Acid Armor':{def:2},
 'Barrier':{def:2},'Work Up':{atk:1,spa:1},'Growth':{atk:1,spa:1},'Hone Claws':{atk:1},
 'Coil':{atk:1,def:1},'Curse':{atk:1,def:1,spe:-1},'Shift Gear':{atk:1,spe:2},
 'Tail Glow':{spa:3},'Belly Drum':{atk:6},'Victory Dance':{atk:1,def:1,spe:1},
 'No Retreat':{atk:1,def:1,spa:1,spd:1,spe:1},'Clangorous Soul':{atk:1,def:1,spa:1,spd:1,spe:1},
};
const stage = n => n >= 0 ? (2 + n) / 2 : 2 / (2 - n);

const only = process.argv.slice(2);
const out = [];
let cells = 0, failed = 0;
const t0 = Date.now();

for (const cp of only) {
  const slots = roster[cp] || [];
  if (!slots.length) continue;
  const defCache = {};
  for (const s of slots) {
    const k = `${s.species}|${s.level}|${s.item}|${s.ability}|${s.nature}|${s.evs}`;
    defCache[k] ||= mk(s.species, s.level, s.item, s.ability, s.nature, arr2(s.evs), arr2(s.ivs));
    s._p = defCache[k];
  }
  for (const b of builds) {
    if (b.checkpoint !== cp) continue;
    const evs = EVOF(b.ev_spread);
    const myMoves = b.moves.split(',');
    const heal = (myMoves.some(m => RECOVERY.has(m)) ? HEAL_RECOVERY : 0)
               + (/regenerator/i.test(b.ability) ? HEAL_REGEN : 0);
    for (const cand of b.item_candidates.split('|')) {
      const [iname, itag, irel] = cand.split(':');
      const me = mk(b.form_key, +b.level, iname, b.ability, 'Hardy', evs, arr2([31,31,31,31,31,31]));
      if (!me) { failed++; continue; }
      const healItem = heal + (itag === 'longevity' ? HEAL_LEFT : 0);
      const setupName = b.setup_move && b.setup_move !== 'NONE' ? b.setup_move : null;
      const boosts = setupName ? SETUP[setupName] : null;
      let boosted = null;
      if (boosts) boosted = mk(b.form_key, +b.level, iname, b.ability, 'Hardy', evs,
                               arr2([31,31,31,31,31,31])), boosted && (boosted.boosts = boosts);
      let sum = 0, wins = 0, n = 0, safe = 0, setupOK = 0;
      const perMove = {};                       // move -> summed margin, for the Choice lock
      for (const s of slots) {
        if (!s._p) continue;
        const o = dmgAll(me, s._p, myMoves);
        const i = dmgAll(s._p, me, s.moves);
        const inc = Math.max(0, i.frac - healItem);
        if (i.frac < 1) safe++;                 // survives a switch-in on their best move
        const spdMe = me.stats.spe * (boosts && boosts.spe ? stage(boosts.spe) : 1);
        const faster = o.priority > i.priority ? 1 : o.priority < i.priority ? 0
                     : (spdMe > s._p.stats.spe ? 1 : 0);
        let margin;
        if (boosts) {
          // the setup turn must be survived, and it costs a turn of incoming damage
          const hpAfter = 1 - i.frac;
          if (hpAfter <= 0) {
            const tU = o.frac > 0 ? Math.ceil(1 / o.frac) : 99;
            const tT = inc > 0 ? Math.ceil(1 / inc) : 99;
            margin = (tT - tU) + (faster ? 0.5 : -0.5) - 1;    // setup fails, turn wasted
          } else {
            setupOK++;
            const ob = boosted ? dmgAll(boosted, s._p, myMoves) : o;
            const tU = ob.frac > 0 ? Math.ceil(1 / ob.frac) : 99;
            const tT = inc > 0 ? Math.ceil(hpAfter / inc) : 99;
            margin = (tT - tU) + (faster ? 0.5 : -0.5);
          }
        } else {
          const tU = o.frac > 0 ? Math.ceil(1 / o.frac) : 99;
          const tT = inc > 0 ? Math.ceil(1 / inc) : 99;
          margin = (tT - tU) + (faster ? 0.5 : -0.5);
        }
        if (CHOICE.has(iname)) {                // locked: one move for the whole roster
          for (const mn in o.per) {
            const tU = o.per[mn].frac > 0 ? Math.ceil(1 / o.per[mn].frac) : 99;
            const tT = inc > 0 ? Math.ceil(1 / inc) : 99;
            (perMove[mn] ||= []).push((tT - tU) + (faster ? 0.5 : -0.5));
          }
        }
        sum += margin; if (margin > 0) wins++; n++; cells++;
      }
      if (!n) continue;
      let locked = null;
      if (CHOICE.has(iname) && Object.keys(perMove).length) {
        locked = Math.max(...Object.values(perMove).map(a => a.reduce((x,y)=>x+y,0)/a.length));
      }
      out.push({checkpoint: cp, form_key: b.form_key, internal_id: b.internal_id, track: b.track,
                item: iname, item_tag: itag, item_reliable: irel === 'T' ? 'TRUE' : 'FALSE',
                mean_margin: +((locked !== null ? locked : sum / n)).toFixed(4),
                unlocked_margin: +(sum / n).toFixed(4),
                choice_locked: locked !== null ? 'TRUE' : 'FALSE',
                win_rate: +(wins / n).toFixed(4),
                switchin_safe_rate: +(safe / n).toFixed(4),
                setup_move: setupName || 'NONE',
                setup_success_rate: boosts ? +(setupOK / n).toFixed(4) : 'NA',
                slots_scored: n, moves: b.moves, ev_spread: b.ev_spread});
    }
  }
  console.error(`  cp${cp} done  cells=${cells}  ${((Date.now()-t0)/1000).toFixed(1)}s`);
}
fs.writeFileSync(`/home/claude/work/${ANCHOR === 'floor' ? 'fl' : 'mx'}_${only.join('_')}.json`, JSON.stringify(out));
console.error(`cells ${cells}  builds failed to construct ${failed}  ${((Date.now()-t0)/1000).toFixed(1)}s`);
