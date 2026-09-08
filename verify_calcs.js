// Verify the engine against an INDEPENDENT reimplementation of the generation-9
// damage formula. If the two agree, mechanics_gen 9 is confirmed and every matrix
// cell inherits a checked assumption rather than an asserted one.
const {calculate, Pokemon, Move, Field} = require('/home/claude/calc/calc/dist/adaptable.js');
const L = require('/home/claude/work/data_layer.js');
const gen = L.gen;

const NAT = {  // nature -> [boosted, hindered]
  Adamant:['atk','spa'], Modest:['spa','atk'], Jolly:['spe','spa'], Timid:['spe','atk'],
  Bold:['def','atk'], Calm:['spd','atk'], Impish:['def','spa'], Careful:['spd','spa'],
  Hardy:[null,null], Serious:[null,null],
};

function statOf(base, iv, ev, lvl, nature, which) {
  const n = NAT[nature] || [null, null];
  let s = Math.floor((Math.floor((2*base + iv + Math.floor(ev/4)) * lvl / 100) + 5));
  if (n[0] === which) s = Math.floor(s * 1.1);
  if (n[1] === which) s = Math.floor(s * 0.9);
  return s;
}
function hpOf(base, iv, ev, lvl) {
  return Math.floor((2*base + iv + Math.floor(ev/4)) * lvl / 100) + lvl + 10;
}

// independent gen-9 damage, no item/ability/weather/crit, single hit, 85..100 roll
function handDamage(att, def, move, lvl) {
  const cat = move.category;
  if (cat === 'Status' || !move.basePower) return null;
  const A = cat === 'Physical'
    ? statOf(att.baseStats.atk, 31, 0, lvl, 'Hardy', 'atk')
    : statOf(att.baseStats.spa, 31, 0, lvl, 'Hardy', 'spa');
  const D = cat === 'Physical'
    ? statOf(def.baseStats.def, 31, 0, lvl, 'Hardy', 'def')
    : statOf(def.baseStats.spd, 31, 0, lvl, 'Hardy', 'spd');
  let base = Math.floor(Math.floor(Math.floor(2*lvl/5 + 2) * move.basePower * A / D) / 50) + 2;
  const stab = att.types.includes(move.type) ? 1.5 : 1;
  let eff = 1;
  for (const t of def.types) eff *= gen.types.get(move.type.toLowerCase()).effectiveness[t];
  if (eff === 0) return [0, 0];
  const out = [];
  for (const r of [85, 100]) {
    let dmg = Math.floor(base * r / 100);
    dmg = Math.floor(dmg * stab);          // pokeRound in-engine; compared with tolerance
    dmg = Math.floor(dmg * eff);
    out.push(Math.max(1, dmg));
  }
  return out;
}

const CASES = [
  ['Charmander','Bulbasaur','Ember',20], ['Squirtle','Charmander','Water Gun',20],
  ['Gyarados','Geodude-Alola','Waterfall',40], ['Alakazam','Machop','Psychic',45],
  ['Tyranitar','Alakazam','Crunch',60], ['Garchomp','Magnezone','Earthquake',68],
  ['Dragapult','Tyranitar','Dragon Darts',85], ['Metagross','Clefable','Meteor Mash',73],
  ['Great Tusk','Gengar','Headlong Rush',68], ['Volcarona','Ferrothorn','Fiery Dance',76],
  ['Kingambit','Hatterene','Kowtow Cleave',85], ['Iron Valiant','Corviknight','Close Combat',80],
];

let ok = 0, off = 0, skipped = 0;
const rows = [];
for (const [a, b, mv, lvl] of CASES) {
  const A = L.spByKey[a], B = L.spByKey[b];
  const M = L.moveById[mv.toLowerCase().replace(/[^a-z0-9]+/g, '')];
  if (!A || !B || !M) { skipped++; rows.push([a, b, mv, 'SKIP: not in target']); continue; }
  const res = calculate(gen,
    new Pokemon(gen, A.name, {level: lvl, nature: 'Hardy', evs: {}, ivs: {}}),
    new Pokemon(gen, B.name, {level: lvl, nature: 'Hardy', evs: {}, ivs: {}}),
    new Move(gen, M.name), new Field());
  const eng = res.damage;
  const engMin = Array.isArray(eng) ? eng[0] : eng;
  const engMax = Array.isArray(eng) ? eng[eng.length-1] : eng;
  const hand = handDamage(A, B, M, lvl);
  if (!hand) { skipped++; rows.push([a, b, mv, 'SKIP: status move']); continue; }
  const dmin = Math.abs(engMin - hand[0]), dmax = Math.abs(engMax - hand[1]);
  const agree = dmin <= 1 && dmax <= 1;
  agree ? ok++ : off++;
  rows.push([`${a} L${lvl}`, b, mv, `engine ${engMin}-${engMax}  hand ${hand[0]}-${hand[1]}  ${agree ? 'agree' : 'DIFFER'}`]);
}
for (const r of rows) console.log('  ' + r[0].padEnd(22) + ' vs ' + r[1].padEnd(16) + r[2].padEnd(16) + r[3]);
console.log(`\nreproduced ${ok}/${ok+off} comparable calcs, ${skipped} skipped`);
console.log(`discrepancy rate ${(100*off/Math.max(1,ok+off)).toFixed(1)}%`);
