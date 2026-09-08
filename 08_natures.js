// CINDER Phase 5 correction — nature enumeration.
// §4.8 says nature is enumerated and scored, never assumed. Every build carried Hardy,
// which made I2 unmeasurable. Candidates are measured against the checkpoint roster with
// the build's already-chosen item, exactly as items were.
const fs = require('fs');
const {calculate, Pokemon, Move, Field} = require('/home/claude/calc/calc/dist/adaptable.js');
const L = require('/home/claude/work/data_layer.js');
const gen = L.gen;
const OUT = '/mnt/user-data/outputs/cinder';
const tsv = p => { const l=fs.readFileSync(p,'utf8').split('\n').filter(Boolean); const h=l[0].split('\t');
  return l.slice(1).map(r=>{const f=r.split('\t');const o={};h.forEach((c,i)=>o[c]=f[i]);return o;}); };

// candidates per track: the natures that plausibly serve that build, not all 25
const CAND = {
  physical:      ['Adamant','Jolly','Naughty','Lonely','Brave','Impish'],
  physical_setup:['Adamant','Jolly','Impish','Careful','Brave','Naughty'],
  special:       ['Modest','Timid','Rash','Mild','Quiet','Calm'],
  special_setup: ['Modest','Timid','Calm','Bold','Quiet','Rash'],
  mixed:         ['Naive','Hasty','Rash','Mild','Quiet','Brave'],
  mixed_setup:   ['Naive','Hasty','Rash','Mild','Quiet','Brave'],
  support:       ['Bold','Calm','Impish','Careful','Relaxed','Sassy'],
  floor:         ['Hardy'],
};
// PRUNING RULE, recorded: nature selection samples at most SAMPLE slots per checkpoint,
// evenly spaced through the roster. Doubling the candidate set while testing every slot was
// not affordable, and a nature's ranking should not hinge on which subset it is tested against.
const SAMPLE = 12;
const EVOF = s => { const m={hp:0,atk:0,def:0,spa:0,spd:0,spe:0};
  const K={HP:'hp',Atk:'atk',Def:'def',SpA:'spa',SpD:'spd',Spe:'spe'};
  for(const p of s.split('/')){const t=p.trim().split(/\s+/); if(t.length===2&&K[t[1]]) m[K[t[1]]]=+t[0];}
  return m; };
const arr2=a=>({hp:a[0],atk:a[1],def:a[2],spa:a[3],spd:a[4],spe:a[5]});
const HEAL_R=0.25,HEAL_G=0.11,HEAL_L=0.0625;
const RECOVERY=new Set(['Recover','Roost','Soft-Boiled','Moonlight','Morning Sun','Synthesis',
 'Slack Off','Milk Drink','Shore Up','Wish','Life Dew','Jungle Healing','Lunar Blessing']);
const LONGEV=new Set(['Leftovers','Black Sludge','Shell Bell','Berry Juice']);

const trainers = tsv(`${OUT}/03_trainers.tsv`).filter(t=>
  t.mode==='normal'&&t.is_level_scaled==='FALSE'&&+t.party_size>=4);
const seq={};
for(const t of trainers) (seq[t.cap_index] ||= []).push(...t.roster.split('|').map(s=>{const f=s.split(':');
  return {species:f[0],level:+f[1],ability:f[3],item:f[4],nature:f[5],
          ivs:f[6].split('/').map(Number),evs:f[7].split('/').map(Number),moves:(f[8]||'').split(',')};}));
const caps={}; for(const t of trainers) caps[t.cap_index]=+t.level_cap;

const mk=(n,l,i,nat,e,v)=>{try{return new Pokemon(gen,n,{level:l,item:i&&i!=='NONE'?i:undefined,
  nature:nat,evs:e,ivs:v});}catch(x){return null;}};
const bestOf=(a,d,mv)=>{let b=0,pr=-7;
  for(const mn of mv){ if(!mn||mn==='NONE')continue;
    const md=L.moveById[mn.toLowerCase().replace(/[^a-z0-9]+/g,'')]; if(!md||!md.basePower)continue;
    let r;try{r=calculate(gen,a,d,new Move(gen,md.name),new Field());}catch(e){continue;}
    const x=r.damage,avg=Array.isArray(x)?(x[0]+x[x.length-1])/2:x,f=avg/d.maxHP();
    if(f>b){b=f;pr=md.priority||0;} }
  return {frac:b,priority:pr};};

const mx=tsv(`${OUT}/04_matchups.tsv`);
const only=process.argv.slice(2); const out=[]; let cells=0; const t0=Date.now();
for(const cp of only){
  let slots=seq[cp]||[]; if(!slots.length) continue;
  if (slots.length > SAMPLE) {
    const step = slots.length / SAMPLE, s2 = [];
    for (let i = 0; i < SAMPLE; i++) s2.push(slots[Math.floor(i*step)]);
    slots = s2;
  }
  const lvl=caps[cp]; const dc={};
  for(const s of slots){const k=`${s.species}|${s.level}|${s.item}|${s.nature}`;
    dc[k] ||= mk(s.species,s.level,s.item,s.nature,arr2(s.evs),arr2(s.ivs)); s._p=dc[k];}
  for(const b of mx){
    if(b.checkpoint!==cp) continue;
    const evs=EVOF(b.ev_spread), iv=arr2([31,31,31,31,31,31]);
    const mv=b.moves.split(',');
    const heal=(mv.some(m=>RECOVERY.has(m))?HEAL_R:0)+(LONGEV.has(b.ceiling_item)?HEAL_L:0);
    let bestNat=null,bestM=-1e9;
    for(const nat of (CAND[b.track]||['Hardy'])){
      const me=mk(b.form_key,lvl,b.ceiling_item,nat,evs,iv); if(!me) continue;
      let sum=0,n=0;
      for(const s of slots){ if(!s._p)continue;
        const o=bestOf(me,s._p,mv), i=bestOf(s._p,me,s.moves); cells++;
        const inc=Math.max(0,i.frac-heal);
        const tU=o.frac>0?Math.ceil(1/o.frac):99, tT=inc>0?Math.ceil(1/inc):99;
        const faster=o.priority>i.priority?1:o.priority<i.priority?0:(me.stats.spe>s._p.stats.spe?1:0);
        sum+=(tT-tU)+(faster?0.5:-0.5); n++; }
      if(n && sum/n>bestM){bestM=sum/n;bestNat=nat;}
    }
    if(bestNat) out.push({checkpoint:cp,internal_id:b.internal_id,track:b.track,
                          nature:bestNat,nature_margin:+bestM.toFixed(4)});
  }
  console.error(`  cp${cp} cells=${cells} ${((Date.now()-t0)/1000).toFixed(1)}s`);
}
fs.writeFileSync(`/home/claude/work/na_${only.join('_')}.json`, JSON.stringify(out));
