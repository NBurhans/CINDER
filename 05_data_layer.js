// CINDER custom data layer.
// The calculator supplies MECHANICS ONLY. Every species, move, ability, item and
// type value below comes from 01_species.tsv / data.json, never from the fork's
// bundled tables. Anything present in the target but absent here is flagged, never
// silently substituted with a vanilla value.
const fs = require('fs');
const {Generations} = require('/home/claude/calc/calc/dist/data/index.js');

const toID = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '');
const D = JSON.parse(fs.readFileSync('/home/claude/work/data.json', 'utf8'));

// ---------- types, from the verified matchup encoding
const EFF = {0: 1, 5: 0.5, 20: 2, 1: 0};
const tyName = {};
for (const k in D.types) tyName[k] = D.types[k].name;
const typeById = {};
for (const k in D.types) {
  const eff = {};
  for (const j in D.types) {
    // types.get(moveType).effectiveness[defenderType] -> this type ATTACKING j
    eff[tyName[j]] = EFF[D.types[k].matchup[Number(j)]];
  }
  typeById[toID(tyName[k])] = {kind: 'Type', id: toID(tyName[k]), name: tyName[k], effectiveness: eff};
}

// ---------- moves
const SPLIT = {0: 'Physical', 1: 'Special', 2: 'Status'};
const moveById = {};
const moveByNum = {};
for (const k in D.moves) {
  const m = D.moves[k];
  const o = {
    kind: 'Move', id: toID(m.name), name: m.name,
    basePower: m.power || 0,
    type: tyName[m.type],
    category: SPLIT[m.split],
    priority: m.priority || 0,
    target: 'normal',
    flags: {},
    secondaries: !!m.secondaryEffectChance,
  };
  if (moveById[o.id]) { o.id = o.id + '_' + k; o.collided = true; }
  moveById[o.id] = o; moveByNum[k] = o;
}

// ---------- abilities and items (names only; mechanics keyed on name)
const abById = {}, abByNum = {};
for (const k in D.abilities) {
  const n = (D.abilities[k].names || ['UNK'])[0];
  const o = {kind: 'Ability', id: toID(n), name: n};
  if (abById[o.id]) { o.id = o.id + '_' + k; o.collided = true; }
  abById[o.id] = o; abByNum[k] = o;
}
const itById = {}, itByNum = {};
for (const k in D.items) {
  const n = D.items[k].name;
  const o = {kind: 'Item', id: toID(n), name: n};
  if (itById[o.id]) { o.id = o.id + '_' + k; o.collided = true; }
  itById[o.id] = o; itByNum[k] = o;
}

// ---------- species, from the Phase 1 table (display order already applied there)
const lines = fs.readFileSync('/mnt/user-data/outputs/cinder/01_species.tsv', 'utf8')
  .split('\n').filter(Boolean);
const head = lines[0].split('\t');
const col = n => head.indexOf(n);
const spById = {}, spByKey = {};
let speciesRows = 0;
for (let i = 1; i < lines.length; i++) {
  const f = lines[i].split('\t');
  const name = f[col('form_key')] && f[col('form_key')] !== 'UNK'
    ? f[col('form_key')] : f[col('species_name')];
  const types = [f[col('type_1')]];
  if (f[col('type_2')] !== 'NONE') types.push(f[col('type_2')]);
  const o = {
    kind: 'Species', id: toID(name), name,
    types,
    baseStats: {
      hp:  +f[col('hp')],  atk: +f[col('atk')], def: +f[col('def')],
      spa: +f[col('spa')], spd: +f[col('spd')], spe: +f[col('spe')],
    },
    nfe: f[col('evolves_into')] !== 'NONE',
    abilities: {0: f[col('ability_1')]},
  };
  if (spById[o.id]) { o.id = o.id + '_' + f[col('internal_id')]; o.collided = true; }
  spById[o.id] = o; spByKey[name] = o; speciesRows++;
}

// natures are pure mechanics, taken from the fork
const vanilla = Generations.get(9);

// WEIGHT. The extracted database does not carry weightkg, and four moves derive their
// base power from it (Low Kick, Grass Knot, Heat Crash, Heavy Slam). Weights are taken
// from the fork's bundled table and are therefore Asserted, not Measured: they are
// vanilla values and this hack could in principle have changed one.
const deaccent = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
let wHit = 0; const wMiss = [];
for (const k in spById) {
  const o = spById[k];
  const v = vanilla.species.get(k) || vanilla.species.get(toID(deaccent(o.name)));
  if (v && v.weightkg > 0) { o.weightkg = v.weightkg; o.weight_source = 'Asserted:fork'; wHit++; }
  else { o.weightkg = null; o.weight_source = 'UNK'; wMiss.push(o.name); }
}

const gen = {
  num: 9,
  species:   {get: id => spById[id],  [Symbol.iterator]: function* () { for (const k in spById) yield spById[k]; }},
  moves:     {get: id => moveById[id], [Symbol.iterator]: function* () { for (const k in moveById) yield moveById[k]; }},
  abilities: {get: id => abById[id],  [Symbol.iterator]: function* () { for (const k in abById) yield abById[k]; }},
  items:     {get: id => itById[id],  [Symbol.iterator]: function* () { for (const k in itById) yield itById[k]; }},
  types:     {get: id => typeById[id], [Symbol.iterator]: function* () { for (const k in typeById) yield typeById[k]; }},
  natures:   vanilla.natures,
};

module.exports = {weight: {hit: wHit, miss: wMiss}, gen, spById, spByKey, moveById, moveByNum, abByNum, itByNum, typeById,
                  counts: {species: speciesRows, moves: Object.keys(moveById).length,
                           abilities: Object.keys(abById).length, items: Object.keys(itById).length,
                           types: Object.keys(typeById).length}};
