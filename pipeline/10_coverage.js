// CINDER Phase 5b — per-slot coverage.
// The team layer needs to know WHICH threats a build answers, not just its aggregate margin.
// The matrix stored aggregates, so this recomputes the per-slot verdict for the recommended
// build of each (checkpoint, form) using the same engine and inputs.
const fs = require('fs');
const {calculate, Pokemon, Move, Field} = require('/home/claude/calc/calc/dist/adaptable.js');
const L = require('/home/claude/work/data_layer.js');
const gen = L.gen;
const OUT = '/mnt/user-data/outputs/cinder';
const tsv = p => { const l=fs.readFileSync(p,'utf8').split('\n').filter(Boolean); const h=l[0].split('\t');
  return l.slice(1).map(r=>{const f=r.split('\t');const o={};h.forEach((c,i)=>o[c]=f[i]);return o;}); };
const EVOF = s => { const m={hp:0,atk:0,def:0,spa:0,spd:0,spe:0};
  const K={HP:'hp',Atk:'atk',Def:'def',SpA:'spa',SpD:'spd',Spe:'spe'};
  for(const p of s.split('/')){const t=p.trim().split(/\s+/); if(t.length===2&&K[t[1]]) m[K[t[1]]]=+t[0];}
  return m; };
const arr2=a=>({hp:a[0],atk:a[1],def:a[2],spa:a[3],spd:a[4],spe:a[5]});
const HEAL_R=0.25, HEAL_L=0.0625;
const RECOVERY=new Set(['Recover','Roost','Soft-Boiled','Moonlight','Morning Sun','Synthesis',
 'Slack Off','Milk Drink','Shore Up','Wish','Life Dew','Jungle Healing','Lunar Blessing']);
const LONGEV=new Set(['Leftovers','Black Sludge','Shell Bell','Berry Juice']);

const trainers = tsv(`${OUT}/03_trainers.tsv`).filter(t=>
  t.mode==='normal'&&t.is_level_scaled==='FALSE'&&+t.party_size>=4);
const seq={}, caps={};
for(const t of trainers){ caps[t.cap_index]=+t.level_cap;
  (seq[t.cap_index] ||= []).push(...t.roster.split('|').map(s=>{const f=s.split(':');
    return {trainer:t.trainer_id,species:f[0],level:+f[1],ability:f[3],item:f[4],nature:f[5],
            ivs:f[6].split('/').map(Number),evs:f[7].split('/').map(Number),moves:(f[8]||'').split(',')};}));}

// the recommended build per (checkpoint, form): highest role_fit in the valuation table
const val = tsv(`${OUT}/05_valuation.tsv`).filter(r=>r.vorp!=='UNK');
const rec = {};
for(const r of val){ const k=`${r.checkpoint}|${r.internal_id}`;
  if(!rec[k] || +r.role_fit > +rec[k].role_fit) rec[k]=r; }

const mk=(n,l,i,nat,e,v)=>{try{return new Pokemon(gen,n,{level:l,item:i&&i!=='NONE'?i:undefined,
  nature:nat||'Hardy',evs:e,ivs:v});}catch(x){return null;}};
const bestOf=(a,d,mv)=>{let b=0,pr=-7;
  for(const mn of mv){ if(!mn||mn==='NONE')continue;
    const md=L.moveById[mn.toLowerCase().replace(/[^a-z0-9]+/g,'')]; if(!md||!md.basePower)continue;
    let r;try{r=calculate(gen,a,d,new Move(gen,md.name),new Field());}catch(e){continue;}
    const x=r.damage,avg=Array.isArray(x)?(x[0]+x[x.length-1])/2:x,f=avg/d.maxHP();
    if(f>b){b=f;pr=md.priority||0;} }
  return {frac:b,priority:pr};};

const only=process.argv.slice(2); const out=[]; let cells=0; const t0=Date.now();
for(const cp of only){
  const slots=seq[cp]||[]; if(!slots.length) continue;
  const lvl=caps[cp], dc={};
  for(const s of slots){const k=`${s.species}|${s.level}|${s.item}|${s.nature}`;
    dc[k] ||= mk(s.species,s.level,s.item,s.nature,arr2(s.evs),arr2(s.ivs)); s._p=dc[k];}
  for(const k in rec){
    const b=rec[k]; if(b.checkpoint!==cp) continue;
    const mv=b.moves.split(',');
    const me=mk(b.form_key,lvl,b.ceiling_item,b.nature,EVOF('252 Atk / 252 Spe / 6 HP'),
                arr2([31,31,31,31,31,31]));
    if(!me) continue;
    const heal=(mv.some(m=>RECOVERY.has(m))?HEAL_R:0)+(LONGEV.has(b.ceiling_item)?HEAL_L:0);
    const margins=[];
    for(const s of slots){ if(!s._p){margins.push(-99);continue;}
      const o=bestOf(me,s._p,mv), i=bestOf(s._p,me,s.moves); cells++;
      const inc=Math.max(0,i.frac-heal);
      const tU=o.frac>0?Math.ceil(1/o.frac):99, tT=inc>0?Math.ceil(1/inc):99;
      const faster=o.priority>i.priority?1:o.priority<i.priority?0:(me.stats.spe>s._p.stats.spe?1:0);
      margins.push(+(((tT-tU)+(faster?0.5:-0.5))).toFixed(2)); }
    out.push({cp, id:b.internal_id, form:b.form_key, item:b.ceiling_item,
              role:b.role, vorp:+b.vorp, m:margins});
  }
  console.error(`  cp${cp} builds=${out.length} cells=${cells} ${((Date.now()-t0)/1000).toFixed(1)}s`);
}
fs.writeFileSync(`/home/claude/work/cv_${only.join('_')}.json`, JSON.stringify(out));
