// CINDER Phase 5 — the sustain axis.
//
// Walk each boss roster SEQUENTIALLY on one lifebar, in the order the fight presents it.
// Reset the bar at every trainer boundary, because the player heals between fights.
// Depth reached before fainting is the raw measure; what gets published is the KIT DELTA
// (this build minus the same form with no kit), because raw depth tracks BST.
//
// Turns-to-KO and incoming damage are computed here from the same engine and inputs the
// matrix used — the matrix stored aggregates, not per-slot cells, so this recomputes the
// per-slot quantities rather than reading them. That is a deviation from the vision's
// "read them off the matrix" and it is logged as such.
const fs = require('fs');
const {calculate, Pokemon, Move, Field} = require('/home/claude/calc/calc/dist/adaptable.js');
const L = require('/home/claude/work/data_layer.js');
const gen = L.gen;
const OUT = '/mnt/user-data/outputs/cinder';
const tsv = p => { const l = fs.readFileSync(p,'utf8').split('\n').filter(Boolean); const h=l[0].split('\t');
  return l.slice(1).map(r=>{const f=r.split('\t');const o={};h.forEach((c,i)=>o[c]=f[i]);return o;}); };

const HEAL_RECOVERY=0.25, HEAL_REGEN=0.11, HEAL_LEFT=0.0625;
const RECOVERY = new Set(['Recover','Roost','Soft-Boiled','Moonlight','Morning Sun','Synthesis',
 'Slack Off','Milk Drink','Shore Up','Wish','Life Dew','Jungle Healing','Lunar Blessing']);
const LONGEV = new Set(['Leftovers','Black Sludge','Shell Bell','Berry Juice']);
const EVOF = s => { const m={hp:0,atk:0,def:0,spa:0,spd:0,spe:0};
  const K={HP:'hp',Atk:'atk',Def:'def',SpA:'spa',SpD:'spd',Spe:'spe'};
  for (const p of s.split('/')) { const t=p.trim().split(/\s+/); if(t.length===2&&K[t[1]]) m[K[t[1]]]=+t[0]; }
  return m; };
const arr2 = a => ({hp:a[0],atk:a[1],def:a[2],spa:a[3],spd:a[4],spe:a[5]});

const trainers = tsv(`${OUT}/03_trainers.tsv`).filter(t =>
  t.mode==='normal' && t.is_level_scaled==='FALSE' && +t.party_size>=4);
const seq = {};                                    // cp -> [{trainer, slot...}] in roster order
for (const t of trainers) {
  (seq[t.cap_index] ||= []).push(...t.roster.split('|').map(s=>{ const f=s.split(':');
    return {trainer:t.trainer_id, species:f[0], level:+f[1], ability:f[3], item:f[4],
            nature:f[5], ivs:f[6].split('/').map(Number), evs:f[7].split('/').map(Number),
            moves:(f[8]||'').split(',')}; }));
}
const mk=(n,l,i,a,nat,e,v)=>{ try{ return new Pokemon(gen,n,{level:l,
  item:i&&i!=='NONE'?i:undefined, ability:a&&a!=='NONE'?a:undefined, nature:nat||'Hardy',
  evs:e, ivs:v}); }catch(x){ return null; } };
const bestFrac=(att,def,moves)=>{ let b=0;
  for(const mn of moves){ if(!mn||mn==='NONE') continue;
    const md=L.moveById[mn.toLowerCase().replace(/[^a-z0-9]+/g,'')]; if(!md||!md.basePower) continue;
    let r; try{ r=calculate(gen,att,def,new Move(gen,md.name),new Field()); }catch(e){ continue; }
    const d=r.damage; const avg=Array.isArray(d)?(d[0]+d[d.length-1])/2:d;
    const f=avg/def.maxHP(); if(f>b) b=f; }
  return b; };

// the ceiling to walk: best-margin build per (checkpoint, form)
const mx = tsv(`${OUT}/04_matchups.tsv`);
const best = {};
for (const r of mx) { const k=`${r.checkpoint}|${r.internal_id}`;
  if(!best[k] || +r.mean_margin > +best[k].mean_margin) best[k]=r; }

const only = process.argv.slice(2);
const out=[]; let cells=0; const t0=Date.now();
for (const cp of only) {
  const slots = seq[cp]||[]; if(!slots.length) continue;
  const dc={};
  for(const s of slots){ const k=`${s.species}|${s.level}|${s.item}|${s.ability}|${s.nature}|${s.evs}`;
    dc[k] ||= mk(s.species,s.level,s.item,s.ability,s.nature,arr2(s.evs),arr2(s.ivs)); s._p=dc[k]; }
  for (const k in best) {
    const b = best[k]; if (b.checkpoint !== cp) continue;
    const iv = arr2([31,31,31,31,31,31]);
    const kit  = mk(b.form_key,+ (b.level||0) || +slots[0].level, b.ceiling_item, null,'Hardy', EVOF(b.ev_spread), iv);
    const bare = mk(b.form_key,+ (b.level||0) || +slots[0].level, 'NONE', null,'Hardy',
                    arr2([0,0,0,0,0,0]), iv);
    if(!kit||!bare) continue;
    const mvKit=b.moves.split(','), mvBare=mvKit;   // bare = same form, no item, no EVs
    const healKit=(mvKit.some(m=>RECOVERY.has(m))?HEAL_RECOVERY:0)+(LONGEV.has(b.ceiling_item)?HEAL_LEFT:0);
    const walk=(mon,mv,heal)=>{ let hp=1,dep=0,cur=null;
      for(const s of slots){ if(!s._p) continue;
        if(s.trainer!==cur){ cur=s.trainer; hp=1; }
        const o=bestFrac(mon,s._p,mv), i=bestFrac(s._p,mon,s.moves); cells++;
        const tk=o>0?Math.ceil(1/o):99;
        const loss=Math.max(0,tk*i - tk*heal);
        if(hp-loss<=0) continue;                    // faints here; next trainer is a fresh bar
        hp-=loss; dep++; }
      return dep; };
    const dKit=walk(kit,mvKit,healKit), dBare=walk(bare,mvBare,0);
    out.push({checkpoint:cp, internal_id:b.internal_id, form_key:b.form_key,
              sustain_depth:dKit, sustain_bare:dBare, sustain_kit_delta:dKit-dBare,
              slots_in_checkpoint:slots.length});
  }
  console.error(`  cp${cp} cells=${cells} ${((Date.now()-t0)/1000).toFixed(1)}s`);
}
fs.writeFileSync(`/home/claude/work/su_${only.join('_')}.json`, JSON.stringify(out));
