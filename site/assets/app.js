(() => {
'use strict';

const O = window.CPE_OBSERVATIONS || [];
const S = window.CPE_SOURCES || [];
const Q = window.CPE_QA || [];
const META = window.CPE_META || {};
const MR = window.CPE_MEASURE_REGISTRY || [];
const CR = window.CPE_CONCEPT_REGISTRY || [];
const SM = window.CPE_SOURCE_MEASURE_MAP || [];
const REL = window.CPE_SOURCE_RELATIONSHIPS || [];
const EQ = window.CPE_EQUIVALENCE_GROUPS || [];
const COV = window.CPE_SOURCE_CONCEPT_COVERAGE || [];
const JREG = window.CPE_JURISDICTIONS || [];
const SYNC = window.CPE_SYNC_AUDIT || [];
const FC = window.CPE_FACILITY_CROSSWALK || [];
const WORLD = window.CPE_WORLD_OUTLINE || {lon:[],lat:[]};

const PAL = 'Mandatory Palestine';
const PAL_HE = 'פלסטין';
const PAL_COLOR = '#a46127';
const COLORS = ['#315f4d','#527289','#934f55','#77658f','#4f7a78','#927637','#537d5f','#765244','#957b58','#596f8b','#8b5e75','#657952'];
const GRADE_RANK = {A:0,B:1,C:2,U:3,D:4};
const SOURCE_TIER = {'official_publication':0,'research_compilation':1,'research_replication':1,'peer_reviewed_research_table':2,'secondary_structured_database':3,'structured_repository_or_microdata':4,'other':5};
const $ = q => document.querySelector(q);
const $$ = q => [...document.querySelectorAll(q)];
const esc = x => String(x ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const n = x => { const v = Number(x); return Number.isFinite(v) ? v : null; };
const fmt = x => n(x) === null ? '—' : new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(n(x));
const pct = x => n(x) === null ? '—' : `${new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(n(x))}%`;
const uniq = a => [...new Set((a||[]).filter(x => x !== null && x !== undefined && x !== ''))];
const mean = a => a.length ? a.reduce((s,x)=>s+x,0)/a.length : null;
const sum = a => a.reduce((s,x)=>s+x,0);
const asBool = x => ['true','1','yes'].includes(String(x).toLowerCase());
const groupBy = (rows,keyFn) => rows.reduce((d,r)=>{ const k=keyFn(r); (d[k] ||= []).push(r); return d; },{});
const downloadRows = (rows,name) => {
  if(!rows || !rows.length) return;
  const cols = uniq(rows.flatMap(r=>Object.keys(r)));
  const lines = [cols.join(',')];
  for(const r of rows) lines.push(cols.map(c=>'"'+String(r[c]??'').replaceAll('"','""')+'"').join(','));
  const blob = new Blob(['\ufeff'+lines.join('\n')],{type:'text/csv;charset=utf-8'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),800);
};

const sourceById = Object.fromEntries(S.map(x=>[x.source_id,x]));
const measureById = Object.fromEntries(MR.map(x=>[x.measure,x]));
const conceptById = Object.fromEntries(CR.map(x=>[x.concept_id,x]));
const jurByName = Object.fromEntries(JREG.map(x=>[x.jurisdiction,x]));
const obsById = Object.fromEntries(O.map(x=>[x.observation_id,x]));
const chartHealth = {};

const state = {
  activeView:'palestine', palTab:'system', atlasTab:'sources', selectedSource:null,
  dataRows:[], dataPage:0, dataPageSize:100, compareRows:[], comparePoints:[],
  currentMeasure:null, sourceRows:[]
};

const plotCfg = {responsive:true,displaylogo:false,displayModeBar:false,scrollZoom:false};
const baseLayout = {paper_bgcolor:'transparent',plot_bgcolor:'transparent',font:{family:'Arial, sans-serif',color:'#26332d',size:11},hovermode:'closest',margin:{l:58,r:24,t:18,b:52},xaxis:{gridcolor:'#e7ebe8',zeroline:false,automargin:true},yaxis:{gridcolor:'#e7ebe8',zeroline:false,automargin:true},legend:{orientation:'h',y:-.2,x:0}};

function measureLabel(m){ return measureById[m]?.label_he || String(m||'').replace(/^source_specific__/,'').replaceAll('_',' '); }
function conceptLabel(c){ return conceptById[c]?.concept_label_he || c; }
function sourceName(sid){ return sourceById[sid]?.name || sid; }
function jurLabel(j){ return j===PAL ? `★ ${PAL_HE}` : j; }
function valueOf(r){ return n(r?.value); }
function numeric(rows=O){ return rows.filter(r=>valueOf(r)!==null && n(r.year)!==null); }
function sourceScore(r){
  const s=sourceById[r.source_dataset]||{};
  return (GRADE_RANK[r.comparability_grade]??9)*100 + (asBool(r.definition_verified)?0:18) + (SOURCE_TIER[s.source_family]??7)*4 + (String(r.quality_flag||'').includes('critical')?30:0);
}
function bestObservation(rows){ return [...rows].sort((a,b)=>sourceScore(a)-sourceScore(b))[0] || null; }
function preferRows(rows, keyFields=['jurisdiction','year','geography_level','geography_name','facility_id','facility_name','measure','legal_status','sex','age_group','sentence_band','labour_status']){
  const mp=new Map();
  for(const r of rows){
    const k=keyFields.map(f=>String(r[f]??'')).join('|');
    const old=mp.get(k); if(!old || sourceScore(r)<sourceScore(old)) mp.set(k,r);
  }
  return [...mp.values()];
}
function filterRows(filters={}){
  return O.filter(r=>Object.entries(filters).every(([k,v])=>{
    if(v===null || v===undefined || v==='' || v==='all') return true;
    if(Array.isArray(v)) return v.includes(r[k]);
    return r[k]===v;
  }));
}
function systemRows(jur,measure){
  return preferRows(numeric(O).filter(r=>r.jurisdiction===jur && r.measure===measure && r.geography_level==='system')).sort((a,b)=>n(a.year)-n(b.year));
}
function facilityRows(measure, predicate=()=>true){
  return numeric(O).filter(r=>r.jurisdiction===PAL && r.measure===measure && r.geography_level==='facility' && predicate(r));
}
function point(r,name){ return {x:n(r.year),y:valueOf(r),name:name||measureLabel(r.measure),ids:[r.observation_id],rows:[r],unit:r.unit||'',grade:r.comparability_grade||'U',formula:'',timeBasis:r.time_basis||'',measure:r.measure}; }
function points(rows,nameFn=r=>measureLabel(r.measure)){ return preferRows(rows).map(r=>point(r,nameFn(r))); }
function flattenRows(points){ return uniq((points||[]).flatMap(p=>(p.rows||[]).map(r=>r.observation_id))).map(id=>obsById[id]).filter(Boolean); }
function periodText(points){ const ys=uniq(points.map(p=>n(p.x))).filter(x=>x!==null).sort((a,b)=>a-b); return ys.length ? `${ys[0]}–${ys[ys.length-1]}` : '—'; }
function modeLabel(mode){ return ({annual:'שנתי',ma3:'ממוצע נע 3 שנים',ma5:'ממוצע נע 5 שנים',periodavg:'ממוצע רב־שנתי',index:'Index 100',change:'שינוי מצטבר'})[mode]||mode; }
function seriesNames(points){ return uniq(points.map(p=>p.name)); }
function inPeriod(points,y0,y1){ return points.filter(p=>n(p.x)!==null && p.x>=y0 && p.x<=y1); }

function transformPoints(input,mode,y0,y1){
  const p=inPeriod(input,y0,y1);
  if(mode==='annual') return p;
  const groups=groupBy(p,x=>x.name);
  const out=[];
  if(mode==='periodavg'){
    for(const [name,pp] of Object.entries(groups)){
      if(!pp.length) continue;
      out.push({x:name,y:mean(pp.map(x=>x.y)),name,ids:uniq(pp.flatMap(x=>x.ids)),rows:flattenRows(pp),unit:pp[0].unit,grade:'B',measure:pp[0].measure,timeBasis:pp[0].timeBasis,formula:`ממוצע אריתמטי של ${pp.length} observations זמינים (${periodText(pp)})`});
    }
    return out;
  }
  if(mode==='index' || mode==='change'){
    for(const [name,pp0] of Object.entries(groups)){
      const pp=[...pp0].sort((a,b)=>a.x-b.x), base=pp[0]?.y;
      if(!base) continue;
      for(const x of pp) out.push({...x,y:mode==='index'?100*x.y/base:100*(x.y-base)/base,unit:mode==='index'?'index':'percent',formula:`${mode==='index'?'Index 100':'שינוי באחוזים'}: בסיס ${pp[0].x} = ${fmt(base)}`});
    }
    return out;
  }
  const windowSize=mode==='ma5'?5:3, minimum=mode==='ma5'?3:2;
  for(const [name,pp0] of Object.entries(groups)){
    const pp=[...pp0].sort((a,b)=>a.x-b.x);
    for(const x of pp){
      const window=pp.filter(z=>z.x>=x.x-windowSize+1 && z.x<=x.x);
      if(window.length<minimum) continue;
      out.push({...x,y:mean(window.map(z=>z.y)),ids:uniq(window.flatMap(z=>z.ids)),rows:flattenRows(window),grade:'B',formula:`ממוצע נע אחורי ${windowSize} שנים; ${window.length} observations זמינים`});
    }
  }
  return out;
}
function ratioSeries(jur,numMeasure,denMeasure,mult,name){
  const years=uniq(systemRows(jur,numMeasure).map(r=>n(r.year))).sort((a,b)=>a-b),out=[];
  for(const y of years){
    const a=bestObservation(systemRows(jur,numMeasure).filter(r=>n(r.year)===y));
    const b=bestObservation(systemRows(jur,denMeasure).filter(r=>n(r.year)===y));
    if(a&&b&&valueOf(b)!==0) out.push({x:y,y:valueOf(a)/valueOf(b)*mult,name,ids:[a.observation_id,b.observation_id],rows:[a,b],unit:mult===100?'percent':'ratio',grade:'B',measure:`${numMeasure}/${denMeasure}`,timeBasis:'derived_ratio',formula:`${measureLabel(numMeasure)} / ${measureLabel(denMeasure)}${mult!==1?` × ${mult}`:''}`});
  }
  return out;
}
function rateSeries(jur,measure,name=jurLabel(jur)){
  const out=[];
  for(const r of systemRows(jur,measure)){
    const d=bestObservation(systemRows(jur,'population_denominator').filter(x=>n(x.year)===n(r.year)));
    if(d&&valueOf(d)>0) out.push({x:n(r.year),y:100000*valueOf(r)/valueOf(d),name,ids:[r.observation_id,d.observation_id],rows:[r,d],unit:'per 100,000',grade:'B',measure:`derived:${measure}:per100k`,timeBasis:r.time_basis,formula:`${measureLabel(measure)} / אוכלוסייה כללית × 100,000`});
  }
  return out;
}
function yoySeries(input,nameSuffix=' — שינוי שנתי'){
  const out=[];
  for(const [name,pp0] of Object.entries(groupBy(input,x=>x.name))){
    const pp=[...pp0].sort((a,b)=>a.x-b.x);
    for(let i=1;i<pp.length;i++){
      if(!pp[i-1].y) continue;
      out.push({...pp[i],name:name+nameSuffix,y:100*(pp[i].y-pp[i-1].y)/pp[i-1].y,unit:'percent',ids:uniq([...(pp[i-1].ids||[]),...(pp[i].ids||[])]),rows:flattenRows([pp[i-1],pp[i]]),formula:`שינוי % מן observation הקודם (${pp[i-1].x})`});
    }
  }
  return out;
}

function chartError(id,message){
  const el=$('#'+id); if(el) el.innerHTML=`<div class="render-error"><div><b>הגרף לא נטען</b><br>${esc(message)}</div></div>`;
  chartHealth[id]={status:'render_error',message,count:0}; renderChartHealth();
}
function chartGap(id,message){
  const el=$('#'+id); if(el) el.innerHTML=`<div class="data-gap"><div><b>אין נתונים מתאימים</b><br>${esc(message)}</div></div>`;
  const meta=$('#meta-'+id); if(meta) meta.innerHTML='<span class="meta-pill">פער נתונים</span>';
  const src=$('#src-'+id); if(src) src.innerHTML='';
  chartHealth[id]={status:'data_gap',message,count:0}; renderChartHealth();
}
function sourceFooter(id,pts,method=''){
  const el=$('#src-'+id); if(!el) return;
  const rows=flattenRows(pts), ids=uniq(rows.map(r=>r.source_dataset));
  if(!ids.length){ el.innerHTML=''; return; }
  el.innerHTML='<b>מקורות:</b> '+ids.map(sid=>`<button class="source-chip" data-source="${esc(sid)}">${esc(sourceName(sid))}</button>`).join('')+(method?`<span>${esc(method)}</span>`:'');
  el.querySelectorAll('[data-source]').forEach(b=>b.onclick=()=>openSource(b.dataset.source));
}
function chartMeta(id,pts,mode,extra=''){
  const el=$('#meta-'+id); if(!el) return;
  const rows=flattenRows(pts), years=uniq(rows.map(r=>n(r.year))).filter(x=>x!==null).sort((a,b)=>a-b), grades=uniq(rows.map(r=>r.comparability_grade)), bases=uniq(rows.map(r=>r.time_basis));
  const items=[`תצוגה: ${modeLabel(mode)}`,`כיסוי: ${years.length?`${years[0]}–${years[years.length-1]}`:'—'}`,`${rows.length} observations`,grades.length?`Grade ${grades.join('/')}`:'',bases.length?`בסיס זמן: ${bases.join(' / ')}`:'',extra].filter(Boolean);
  el.innerHTML=items.map(x=>`<span class="meta-pill">${esc(x)}</span>`).join('');
}
function traceData(pts,{type='scatter',stack=false,secondaryNames=[]}={}){
  const names=seriesNames(pts);
  return names.map((name,i)=>{
    const pp=pts.filter(p=>p.name===name).sort((a,b)=>String(a.x).localeCompare(String(b.x),undefined,{numeric:true}));
    const isPal=name===PAL_HE||name===PAL||name.includes('פלסטין'), secondary=secondaryNames.includes(name);
    const trace={type, name, x:pp.map(p=>p.x), y:pp.map(p=>p.y), customdata:pp.map(p=>JSON.stringify({ids:p.ids||[],formula:p.formula||'',title:name,measure:p.measure||''})), hovertemplate:`<b>${esc(name)}</b><br>%{x}: %{y:,.2f}<br><span style="font-size:10px">לחצו לפרטי המקור</span><extra></extra>`};
    if(type==='scatter'){
      trace.mode='lines+markers'; trace.line={color:isPal?PAL_COLOR:COLORS[i%COLORS.length],width:isPal?4:2.2}; trace.marker={color:isPal?PAL_COLOR:COLORS[i%COLORS.length],size:isPal?8:6};
      if(stack) trace.stackgroup='one';
    } else trace.marker={color:isPal?PAL_COLOR:COLORS[i%COLORS.length],line:{color:'#fff',width:.5}};
    if(secondary) trace.yaxis='y2';
    return trace;
  });
}
function bindPlotClick(id,title){
  const el=$('#'+id); if(!el || !el.on) return;
  try{ el.removeAllListeners?.('plotly_click'); }catch(_){ }
  el.on('plotly_click',ev=>{
    const raw=ev?.points?.[0]?.customdata; if(!raw) return;
    try{ const d=JSON.parse(raw); showObservationDrawer(d.ids||[],title,d.formula||''); }catch(_){ }
  });
}
function safePlot(id,pts,layout={},options={}){
  if(!$('#'+id)) return false;
  if(!pts || !pts.length){ chartGap(id,options.empty||'אין observations בטווח או בהגדרה שנבחרו.'); return false; }
  try{
    const traces=traceData(pts,{type:options.type||'scatter',stack:!!options.stack,secondaryNames:options.secondaryNames||[]});
    let lay={...baseLayout,...layout};
    if(options.secondaryNames?.length) lay={...lay,yaxis:{...(lay.yaxis||{}),title:options.primaryAxis||''},yaxis2:{overlaying:'y',side:'right',showgrid:false,zeroline:false,title:options.secondaryAxis||''}};
    Plotly.react(id,traces,lay,plotCfg); bindPlotClick(id,options.title||'גרף');
    chartHealth[id]={status:'ok',message:`${pts.length} points`,count:pts.length}; renderChartHealth(); return true;
  }catch(e){ chartError(id,e.message||String(e)); return false; }
}
function safeHeatmap(id,x,y,z,layout={},hover=''){
  if(!x.length||!y.length){ chartGap(id,'אין מספיק נתונים למטריצה.'); return false; }
  try{
    // Plotly heatmap raster layers can produce NaN image heights in static/local
    // environments. A square-marker matrix is visually equivalent, remains fully
    // interactive, and is stable on file:// and GitHub Pages.
    const xx=[],yy=[],zz=[];
    for(let i=0;i<y.length;i++) for(let j=0;j<x.length;j++){ xx.push(x[j]); yy.push(y[i]); zz.push(n(z?.[i]?.[j])??0); }
    const maxZ=Math.max(...zz,1),markerSize=Math.max(5,Math.min(14,Math.floor(620/Math.max(x.length,1))));
    const trace={type:'scatter',mode:'markers',x:xx,y:yy,customdata:zz,marker:{symbol:'square',size:markerSize,color:zz,cmin:0,cmax:maxZ,colorscale:[[0,'#f3f2ee'],[.01,'#e6eee9'],[1,'#315f4d']],showscale:false,line:{width:0}},hovertemplate:hover||'%{y}<br>%{x}: %{customdata}<extra></extra>',showlegend:false};
    const stableHover=(hover||'%{y}<br>%{x}: %{z}<extra></extra>').replaceAll('%{z}','%{customdata}'); trace.hovertemplate=stableHover;
    Plotly.react(id,[trace],{...baseLayout,...layout,xaxis:{...(baseLayout.xaxis||{}),...(layout.xaxis||{}),type:'category'},yaxis:{...(baseLayout.yaxis||{}),...(layout.yaxis||{}),type:'category'}},plotCfg);
    chartHealth[id]={status:'ok',message:`${x.length}×${y.length} matrix`,count:x.length*y.length}; renderChartHealth(); return true;
  }catch(e){ chartError(id,e.message||String(e)); return false; }
}
function renderSeries(id,basePts,mode,y0,y1,layout={},options={}){
  const pts=transformPoints(basePts,mode,y0,y1);
  const type=mode==='periodavg'?'bar':(options.type||'scatter');
  const ok=safePlot(id,pts,layout,{...options,type});
  if(ok){ chartMeta(id,pts,mode,options.meta||''); sourceFooter(id,pts,options.method||''); }
  return pts;
}

function openDrawer(){ $('#drawer').classList.add('open'); $('#drawerBackdrop').classList.remove('hidden'); }
function closeDrawer(){ $('#drawer').classList.remove('open'); $('#drawerBackdrop').classList.add('hidden'); }
function kv(items){ return `<div class="kv">${items.map(([k,v])=>`<b>${esc(k)}</b><span>${v||'—'}</span>`).join('')}</div>`; }
function showObservationDrawer(ids,title='Observation',formula=''){
  const rows=uniq(ids).map(id=>obsById[id]).filter(Boolean);
  if(!rows.length) return;
  const primary=rows[0], source=sourceById[primary.source_dataset]||{};
  const related=O.filter(r=>r.jurisdiction===primary.jurisdiction && n(r.year)===n(primary.year) && r.concept_id===primary.concept_id && !ids.includes(r.observation_id)).slice(0,20);
  const exact=EQ.filter(g=>String(g.observation_ids||'').split(' | ').some(id=>ids.includes(id)));
  const relSources=REL.filter(x=>x.source_a===primary.source_dataset || x.source_b===primary.source_dataset).slice(0,12);
  const boxes=rows.map(r=>`<div class="observation-box ${r.jurisdiction===PAL?'pal':''}"><b>${esc(measureLabel(r.measure))} · ${esc(r.year)}</b>${kv([
    ['מרחב',jurLabel(r.jurisdiction)],['ערך',`${fmt(r.value)} ${esc(r.unit||'')}`],['רמה',`${esc(r.geography_level||'')} · ${esc(r.facility_name||r.geography_name||'')}`],['מושג',esc(r.concept_label_he||conceptLabel(r.concept_id))],['בסיס זמן',esc(r.time_basis||'')],['Grade',esc(r.comparability_grade||'')],['שדה מקור',esc(r.source_header||r.source_column||'')],['מיקום במקור',esc(r.source_locator||r.source_table||'')],['Record ID',esc(r.source_record_id||'')],['Transformation',esc(r.transformation||'')],['Quality',esc(r.quality_flag||'')],['הערה',esc(r.notes||'')]
  ])}</div>`).join('');
  $('#drawerContent').innerHTML=`<div class="eyebrow">DATA LINEAGE</div><h2>${esc(title)}</h2>${formula?`<div class="callout info"><b>חישוב:</b> ${esc(formula)}</div>`:''}${boxes}
  <div class="drawer-actions"><button id="drawerData">פתח בסייר הנתונים</button><button id="drawerCompare">השווה את המושג</button><button id="drawerSource">דף המקור</button>${primary.source_url?`<a target="_blank" href="${esc(primary.source_url)}">פתח מקור חיצוני ↗</a>`:''}</div>
  <div class="drawer-section"><h3>המקור</h3>${kv([['שם',esc(source.name||primary.source_dataset)],['גוף',esc(source.institution||'')],['סטטוס',esc(source.state||'')],['רמת ראיות',esc(source.evidence_tier||'')],['שנים',esc(source.years_available||'')],['פורמט',esc(source.format||'')]])}</div>
  <div class="drawer-section"><h3>Observations קשורים באותה שנה ובאותו מושג</h3>${related.length?related.map(r=>`<button class="related-item detail-button" data-obs="${esc(r.observation_id)}">${esc(measureLabel(r.measure))}: ${fmt(r.value)} ${esc(r.unit||'')} · ${esc(sourceName(r.source_dataset))}</button>`).join(''):'<p>לא נמצאו observations קשורים.</p>'}</div>
  <div class="drawer-section"><h3>חלופות מדויקות</h3>${exact.length?exact.map(g=>`<div class="related-item">${esc(g.sources)} · spread ${fmt(g.absolute_spread)} · ${esc(g.agreement_status)}</div>`).join(''):'<p>אין מקור חלופי שמדווח על אותו measure ובאותם ממדים בדיוק.</p>'}</div>
  <div class="drawer-section"><h3>קשרי מקור</h3>${relSources.length?relSources.map(x=>`<div class="related-item">${esc(x.relation_type)} · ${esc(x.source_a)} ↔ ${esc(x.source_b)} · ${esc(x.concept_id)}</div>`).join(''):'<p>לא נמצאו קשרים נוספים.</p>'}</div>`;
  $('#drawerData').onclick=()=>{ closeDrawer(); setDataFilters({source_dataset:primary.source_dataset,jurisdiction:primary.jurisdiction,measure:primary.measure,year:primary.year}); nav('data'); };
  $('#drawerCompare').onclick=()=>{ closeDrawer(); nav('compare'); $('#cmpConcept').value=primary.concept_id; fillCompareMeasures(); if([...$('#cmpMeasure').options].some(o=>o.value===primary.measure)) $('#cmpMeasure').value=primary.measure; renderCompare(); };
  $('#drawerSource').onclick=()=>{ closeDrawer(); openSource(primary.source_dataset); };
  $$('#drawerContent [data-obs]').forEach(b=>b.onclick=()=>showObservationDrawer([b.dataset.obs],'Observation קשור'));
  openDrawer();
}

function palControls(){ return {y0:n($('#palY0').value)||1920,y1:n($('#palY1').value)||1948,mode:$('#palMode').value}; }
function palSystemPoints(measure,name){ return points(systemRows(PAL,measure),()=>name||measureLabel(measure)); }
function palFacilityPoints(measure,predicate=()=>true,nameFn=r=>r.facility_name){ return points(facilityRows(measure,predicate),nameFn); }
function renderPalestine(){
  const {y0,y1,mode}=palControls();
  $('#palModeNote').innerHTML=mode==='periodavg'?`הגרפים מציגים ממוצע של השנים הזמינות בין <b>${y0}</b> ל־<b>${y1}</b>. מספר ה־observations והכיסוי מוצגים מתחת לכל גרף.`:mode==='ma3'||mode==='ma5'?`${modeLabel(mode)} מחליק תנודות קצרות. החלון הוא אחורי ומוצג רק כאשר יש מספיק observations.`:mode==='index'||mode==='change'?`כל סדרה מחושבת ביחס ל־observation הראשון שלה בתוך ${y0}–${y1}.`:`ערכים שנתיים זמינים בין ${y0} ל־${y1}.`;
  if(state.palTab==='system') renderPalSystem(y0,y1,mode);
  if(state.palTab==='institutions') renderPalInstitutions(y0,y1,mode);
  if(state.palTab==='governance') renderPalGovernance(y0,y1,mode);
  if(state.palTab==='events') renderPalEvents(y0,y1,mode);
}
function renderPalSystem(y0,y1,mode){
  const stock=palSystemPoints('stock_eoy_total','מצבת סוף שנה'),avg=palSystemPoints('avg_daily_total','ממוצע יומי'),adm=palSystemPoints('admissions_total','Admissions');
  const flowPts=[...transformPoints(stock,mode,y0,y1),...transformPoints(avg,mode,y0,y1),...transformPoints(adm,mode,y0,y1)];
  safePlot('pFlowStock',flowPts,{yaxis:{title:'אסירים — stock / average'},yaxis2:{title:'Admissions',overlaying:'y',side:'right',showgrid:false}},{secondaryNames:['Admissions'],title:'פלסטין: flow מול stock',primaryAxis:'אסירים',secondaryAxis:'Admissions'}); chartMeta('pFlowStock',flowPts,mode); sourceFooter('pFlowStock',flowPts,'Admissions הם זרם שנתי; stock וממוצע יומי אינם אותו מדד.');
  const legal=[...palSystemPoints('stock_eoy_convicted','מורשעים'),...palSystemPoints('stock_eoy_nonconvicted','לא־מורשעים'),...palSystemPoints('stock_eoy_debtors','חייבים')];
  const legalT=transformPoints(legal,mode,y0,y1); safePlot('pLegalComposition',legalT,{yaxis:{title:'אסירים'},barmode:'stack'},{type:mode==='periodavg'?'bar':'scatter',stack:mode!=='periodavg',title:'הרכב משפטי'}); chartMeta('pLegalComposition',legalT,mode); sourceFooter('pLegalComposition',legalT);
  const mix=[...palSystemPoints('admissions_convicted','מורשעים'),...palSystemPoints('admissions_safe_custody','Safe custody'),...palSystemPoints('admissions_debtors','חייבים')];
  const mixT=transformPoints(mix,mode,y0,y1); safePlot('pAdmissionsMix',mixT,{yaxis:{title:'Admissions'},barmode:'stack'},{type:mode==='periodavg'?'bar':'scatter',stack:mode!=='periodavg',title:'תמהיל admissions'}); chartMeta('pAdmissionsMix',mixT,mode); sourceFooter('pAdmissionsMix',mixT);
  renderSeries('pTurnover',ratioSeries(PAL,'admissions_total','avg_daily_total',1,'Admissions / average daily'),mode,y0,y1,{yaxis:{title:'יחס'}},{title:'Turnover',method:'נגזר מ־admissions חלקי הממוצע היומי.'});
  const rates=[...palSystemPoints('stock_eoy_rate_per_100000','מצבת סוף שנה ל־100,000'),...palSystemPoints('avg_daily_rate_per_100000','ממוצע יומי ל־100,000'),...palSystemPoints('admissions_rate_per_100000','Admissions ל־100,000')];
  renderSeries('pRates',rates,mode,y0,y1,{yaxis:{title:'ל־100,000'}},{title:'שיעורים לאוכלוסייה'});
  renderSeries('pAverageStockRatio',ratioSeries(PAL,'avg_daily_total','stock_eoy_total',100,'ממוצע יומי / מצבת סוף שנה'),mode,y0,y1,{yaxis:{title:'אחוז'}},{title:'יחס average ל-stock',method:'נגזר מן הממוצע היומי וממצבת סוף השנה.'});
  const annualBase=[...stock,...adm]; const annualT=transformPoints(annualBase,mode,y0,y1); const changes=yoySeries(annualT,'');
  safePlot('pAnnualChange',changes,{yaxis:{title:'שינוי %',zeroline:true}},{title:'שינוי שנתי'}); chartMeta('pAnnualChange',changes,mode,'שינוי בין observations עוקבים'); sourceFooter('pAnnualChange',changes);
}
function renderPalInstitutions(y0,y1,mode){
  const central=r=>r.facility_type==='central_prison';
  renderSeries('pCentralStock',palFacilityPoints('stock_eoy_total',central,r=>r.facility_name),mode,y0,y1,{yaxis:{title:'אסירים'}},{title:'עכו וירושלים — stock'});
  renderSeries('pCentralAdmissions',palFacilityPoints('admissions_total',central,r=>r.facility_name),mode,y0,y1,{yaxis:{title:'Admissions'}},{title:'עכו וירושלים — admissions'});
  const lock=r=>String(r.facility_type||'').startsWith('district_lockup');
  renderSeries('pLockupStock',palFacilityPoints('stock_eoy_total',lock,r=>r.facility_name),mode,y0,y1,{yaxis:{title:'אסירים'}},{title:'Lock-ups — stock'});
  renderSeries('pLockupAdmissions',palFacilityPoints('admissions_total',lock,r=>r.facility_name),mode,y0,y1,{yaxis:{title:'Admissions'}},{title:'Lock-ups — admissions'});
  const det=r=>r.facility_type==='detention_camp';
  const detention=[...palFacilityPoints('detention_stock_eoy',det,r=>r.facility_name),...palFacilityPoints('detention_avg_daily',det,r=>`${r.facility_name} — ממוצע`)];
  renderSeries('pDetention',detention,mode,y0,y1,{yaxis:{title:'עצורים'}},{title:'מחנות מעצר'});
  const rr=facilityRows('stock_eoy_total',()=>true).filter(r=>n(r.year)>=y0&&n(r.year)<=y1), grouped=groupBy(rr,r=>r.facility_name||'לא ידוע');
  const rankPts=Object.entries(grouped).map(([name,g])=>({x:name,y:mean(g.map(valueOf)),name,ids:g.map(r=>r.observation_id),rows:g,unit:'persons',grade:'B',formula:`ממוצע של ${g.length} observations`,measure:'stock_eoy_total'})).sort((a,b)=>b.y-a.y).slice(0,18);
  safePlot('pFacilityRanking',rankPts,{xaxis:{tickangle:-25},yaxis:{title:'ממוצע stock'}},{type:'bar',title:'דירוג מוסדות'}); chartMeta('pFacilityRanking',rankPts,'periodavg'); sourceFooter('pFacilityRanking',rankPts);
  const all=O.filter(r=>r.jurisdiction===PAL&&r.geography_level==='facility'&&n(r.year)>=y0&&n(r.year)<=y1), facilities=uniq(all.map(r=>r.facility_name)).sort(), years=[]; for(let y=y0;y<=y1;y++) years.push(y);
  const z=facilities.map(f=>years.map(y=>all.filter(r=>r.facility_name===f&&n(r.year)===y).length));
  safeHeatmap('pFacilityCoverage',years,facilities,z,{margin:{l:190,r:10,t:10,b:45},yaxis:{automargin:true},xaxis:{dtick:2}},'%{y}<br>%{x}: %{z} observations<extra></extra>');
  $('#meta-pFacilityCoverage').innerHTML=`<span class="meta-pill">כל מדדי המוסדות</span><span class="meta-pill">${all.length} observations</span>`; sourceFooter('pFacilityCoverage',points(all,r=>r.facility_name));
}
function renderPalGovernance(y0,y1,mode){
  const labour=[...palSystemPoints('prison_labour_count','Prison labour count'),...palSystemPoints('employed_avg_daily_total','מועסקים — ממוצע יומי')];
  renderSeries('pLabour',labour,mode,y0,y1,{yaxis:{title:'אסירים'}},{title:'עבודת אסירים'});
  renderSeries('pLabourShare',ratioSeries(PAL,'employed_avg_daily_total','avg_daily_total',100,'מועסקים / ממוצע יומי'),mode,y0,y1,{yaxis:{title:'אחוז'}},{title:'שיעור תעסוקה'});
  renderSeries('pLabourValue',palSystemPoints('prison_labour_value','ערך עבודת אסירים'),mode,y0,y1,{yaxis:{title:'ערך מדווח'}},{title:'ערך עבודת אסירים'});
  const exp=[...palSystemPoints('prison_expenditure_total','סך הוצאה'),...palSystemPoints('prison_expenditure','הוצאה מדווחת')];
  renderSeries('pExpenditure',exp,mode,y0,y1,{yaxis:{title:'מטבע מקורי'}},{title:'הוצאות',meta:'אין לבצע השוואת מטבעות ללא harmonization'});
  const discipline=palSystemPoints('disciplinary_offences','עבירות משמעת');
  const dRate=ratioSeries(PAL,'disciplinary_offences','avg_daily_total',100,'עבירות ל־100 אסיר־שנים');
  const dPts=[...transformPoints(discipline,mode,y0,y1),...transformPoints(dRate,mode,y0,y1)]; safePlot('pDiscipline',dPts,{yaxis:{title:'מספר עבירות'},yaxis2:{title:'ל־100 אסירים',overlaying:'y',side:'right',showgrid:false}},{secondaryNames:['עבירות ל־100 אסיר־שנים'],title:'משמעת'}); chartMeta('pDiscipline',dPts,mode); sourceFooter('pDiscipline',dPts);
  const punishMeasures=[['punishment_corporal','גופנית'],['punishment_solitary','בידוד'],['punishment_forfeiture','שלילת remission'],['punishment_solitary_and_forfeiture','בידוד + שלילה'],['punishment_leg_irons','כבלי רגליים']];
  const punish=punishMeasures.flatMap(([m,l])=>palSystemPoints(m,l)); const punishT=transformPoints(punish,mode,y0,y1); safePlot('pPunishments',punishT,{yaxis:{title:'אירועים'},barmode:'stack'},{type:mode==='periodavg'?'bar':'scatter',stack:mode!=='periodavg',title:'עונשים משמעתיים'}); chartMeta('pPunishments',punishT,mode); sourceFooter('pPunishments',punishT);
  renderSeries('pRecidivismRate',palSystemPoints('recidivism_rate_pct','שיעור רצידיביזם'),mode,y0,y1,{yaxis:{title:'אחוז'}},{title:'שיעור רצידיביזם'});
  const recMix=[...palSystemPoints('recidivists_once','פעם אחת'),...palSystemPoints('recidivists_twice','פעמיים'),...palSystemPoints('recidivists_three_plus','שלוש ומעלה')]; const recT=transformPoints(recMix,mode,y0,y1); safePlot('pRecidivismMix',recT,{yaxis:{title:'אסירים'},barmode:'stack'},{type:mode==='periodavg'?'bar':'scatter',stack:mode!=='periodavg',title:'הרשעות קודמות'}); chartMeta('pRecidivismMix',recT,mode); sourceFooter('pRecidivismMix',recT);
  const sentenceRows=preferRows(numeric(O).filter(r=>r.jurisdiction===PAL&&r.measure==='stock_eoy_sentence_band'&&(r.sex==='unknown_first_block'||!r.sex||r.sex==='all')));
  const sent=points(sentenceRows,r=>r.sentence_band||'לא ידוע'); const sentT=transformPoints(sent,mode,y0,y1); safePlot('pSentences',sentT,{yaxis:{title:'אסירים'},barmode:'stack'},{type:mode==='periodavg'?'bar':'scatter',stack:mode!=='periodavg',title:'אורך עונש'}); chartMeta('pSentences',sentT,mode,'Female block excluded unless explicitly identified'); sourceFooter('pSentences',sentT);
}
function renderPalEvents(y0,y1,mode){
  renderSeries('pEscapesExecutions',[...palSystemPoints('escapes_reported_count','בריחות'),...palSystemPoints('executions','הוצאות להורג')],mode,y0,y1,{yaxis:{title:'אירועים'}},{title:'בריחות והוצאות להורג'});
  renderSeries('pMovements',[...palSystemPoints('extraditions_to_palestine','הסגרות לפלסטין'),...palSystemPoints('extraditions_from_palestine','הסגרות מפלסטין'),...palSystemPoints('deportations','גירושים')],mode,y0,y1,{yaxis:{title:'אנשים'}},{title:'הסגרות וגירושים'});
  renderSeries('pLunatics',palSystemPoints('stock_eoy_criminal_lunatics','Criminal lunatics'),mode,y0,y1,{yaxis:{title:'אנשים'}},{title:'Criminal lunatics'});
  renderSeries('pVisitors',[...palSystemPoints('prison_visitors','מבקרים'),...palSystemPoints('prison_visitor_visits','ביקורים')],mode,y0,y1,{yaxis:{title:'מספר'}},{title:'מבקרי בתי סוהר'});
  const notes=O.filter(r=>r.jurisdiction===PAL&&r.measure==='remarks'&&n(r.year)>=y0&&n(r.year)<=y1).sort((a,b)=>n(a.year)-n(b.year));
  $('#pNotesTimeline').innerHTML=notes.length?notes.map(r=>`<article class="timeline-item"><div class="timeline-year">${esc(r.year)}</div><div><div class="timeline-text">${esc(r.raw_value_text||r.notes||'')}</div><div class="timeline-links"><button class="detail-button" data-note="${esc(r.observation_id)}">מקור ופרטים</button></div></div></article>`).join(''):'<div class="data-gap">אין הערות בטווח שנבחר.</div>';
  $$('#pNotesTimeline [data-note]').forEach(b=>b.onclick=()=>showObservationDrawer([b.dataset.note],'הערת מקור'));
}

const ALIGNMENT = {
  custodial_population_total:['stock_eoy_total','population_point_total'],
  custodial_population_average:['avg_daily_total'],
  admissions_flow:['admissions_total','distinct_persons_received','distinct_convicted_admissions','prisoners_handled_during_year'],
  population_rate:['stock_eoy_rate_per_100000','population_point_rate_per_100000','avg_daily_rate_per_100000','admissions_rate_per_100000','source_reported_avg_daily_rate_per_100000'],
  finance:['expenditure_per_avg_prisoner','expenditure_per_prisoner_day','prison_expenditure_net','prison_expenditure_total','prison_expenditure'],
  recidivism:['recidivism_rate_pct','recidivists_total','recidivists'],
  prison_labour:['employed_avg_daily_total','prison_labour_count','prison_labour_value'],
  movement_and_outcomes:['escapes_reported_count','executions','deportations'],
  capacity_and_occupancy:['prison_capacity']
};
function fillCompareMeasures(){
  const concept=$('#cmpConcept').value, measures=MR.filter(m=>m.concept_id===concept && O.some(r=>r.measure===m.measure));
  $('#cmpMeasure').innerHTML=`<option value="__aligned__">סדרה מיושרת לפי המושג</option>`+measures.map(m=>`<option value="${esc(m.measure)}">${esc(m.label_he)} · ${esc(m.time_basis)}</option>`).join('');
}
function comparisonCandidates(jur,concept,measure,geo,y0,y1){
  let rows=numeric(O).filter(r=>r.jurisdiction===jur&&r.geography_level===geo&&n(r.year)>=y0&&n(r.year)<=y1);
  if(measure!=='__aligned__') rows=rows.filter(r=>r.measure===measure);
  else {
    const pref=ALIGNMENT[concept]||[]; rows=rows.filter(r=>r.concept_id===concept && pref.includes(r.measure));
    const byYear=groupBy(rows,r=>`${r.year}|${r.geography_name||''}|${r.facility_name||''}`),out=[];
    for(const g of Object.values(byYear)){
      let chosen=null;
      for(const m of pref){ const cand=g.filter(r=>r.measure===m); if(cand.length){ chosen=bestObservation(cand); break; } }
      if(chosen) out.push(chosen);
    }
    return out;
  }
  return preferRows(rows);
}
function selectedComparators(){ return uniq([PAL,...$$('#cmpJurisdictions input:checked').map(x=>x.value)]); }
function renderCompare(){
  const concept=$('#cmpConcept').value, measure=$('#cmpMeasure').value, geo=$('#cmpGeo').value, mode=$('#cmpMode').value, y0=n($('#cmpY0').value), y1=n($('#cmpY1').value), jurs=selectedComparators();
  let rows=[]; for(const j of jurs) rows.push(...comparisonCandidates(j,concept,measure,geo,y0,y1));
  let points0=points(rows,r=>jurLabel(r.jurisdiction));
  const palYears=new Set(points0.filter(p=>p.name.includes('פלסטין')).map(p=>p.x));
  if($('#cmpOverlap').checked) points0=points0.filter(p=>palYears.has(p.x));
  const warnings=[];
  if(!palYears.size) warnings.push('לפלסטין אין observation מתאים לבחירה. בחרו מושג, מדד או טווח אחר.');
  const bases=uniq(flattenRows(points0).map(r=>r.time_basis)); if(bases.length>1) warnings.push(`ההשוואה משלבת בסיסי זמן: ${bases.join(' / ')}.`);
  const units=uniq(flattenRows(points0).map(r=>r.unit)); if(units.length>1 && mode!=='index' && mode!=='change') warnings.push(`היחידות אינן אחידות: ${units.join(' / ')}. מומלץ לעבור ל־Index 100.`);
  $('#cmpWarning').classList.toggle('hidden',!warnings.length); $('#cmpWarning').innerHTML=warnings.join('<br>');
  $('#cmpTitle').textContent=`${conceptLabel(concept)} — פלסטין מול המרחבים שנבחרו`;
  const transformed=transformPoints(points0,mode,y0,y1); state.compareRows=flattenRows(points0); state.comparePoints=transformed;
  safePlot('cmpMain',transformed,{yaxis:{title:mode==='index'?'Index':mode==='change'?'שינוי %':units[0]||''}},{type:mode==='periodavg'?'bar':'scatter',title:'השוואה מרכזית'}); chartMeta('cmpMain',transformed,mode); sourceFooter('cmpMain',transformed,measure==='__aligned__'?'כל מרחב הותאם למדד המועדף הזמין באותו מושג.':'השוואת measure זהה.');
  const avg=transformPoints(points0,'periodavg',y0,y1).sort((a,b)=>b.y-a.y); safePlot('cmpAverages',avg,{xaxis:{tickangle:-25}},{type:'bar',title:'ממוצע תקופתי'}); chartMeta('cmpAverages',avg,'periodavg');
  const palByYear=Object.fromEntries(points0.filter(p=>p.name.includes('פלסטין')).map(p=>[p.x,p])); const ratios=[];
  for(const p of points0.filter(p=>!p.name.includes('פלסטין'))){ const q=palByYear[p.x]; if(q&&q.y) ratios.push({...p,y:100*p.y/q.y,ids:uniq([...(p.ids||[]),...(q.ids||[])]),rows:flattenRows([p,q]),unit:'Palestine=100',formula:`${p.name} / פלסטין × 100`}); }
  safePlot('cmpPalRatio',ratios,{yaxis:{title:'פלסטין = 100',zeroline:false}},{title:'יחס לפלסטין'}); chartMeta('cmpPalRatio',ratios,'annual');
  const changes=transformPoints(points0,'change',y0,y1); safePlot('cmpChange',changes,{yaxis:{title:'שינוי %',zeroline:true}},{title:'שינוי מצטבר'}); chartMeta('cmpChange',changes,'change');
  const names=seriesNames(points0), years=[]; for(let y=y0;y<=y1;y++) years.push(y); const z=names.map(name=>years.map(y=>points0.some(p=>p.name===name&&p.x===y)?1:0)); safeHeatmap('cmpCoverage',years,names,z,{margin:{l:145,r:10,t:10,b:42}},'%{y}<br>%{x}: %{z}<extra></extra>'); $('#meta-cmpCoverage').innerHTML=`<span class="meta-pill">1 = observation קיים</span><span class="meta-pill">${points0.length} points</span>`;
  const basis=groupBy(flattenRows(points0),r=>r.jurisdiction); const rowsTable=Object.entries(basis).map(([j,g])=>[jurLabel(j),uniq(g.map(r=>measureLabel(r.measure))).join(' / '),uniq(g.map(r=>r.time_basis)).join(' / '),uniq(g.map(r=>r.comparability_grade)).join('/'),uniq(g.map(r=>sourceName(r.source_dataset))).join(' / '),`${Math.min(...g.map(r=>n(r.year)))}–${Math.max(...g.map(r=>n(r.year)))}`]);
  $('#cmpBasisTable').innerHTML=tableHtml(['מרחב','מדד בפועל','בסיס זמן','Grade','מקורות','כיסוי'],rowsTable);
}

function openSource(sid){
  nav('atlas'); activateAtlasTab('sources'); state.selectedSource=sid; renderSourceDetail(sid); setTimeout(()=>$('#sourceDetail')?.scrollIntoView({behavior:'smooth',block:'start'}),50);
}
function renderSourceCards(){
  const q=String($('#sourceSearch').value||'').toLowerCase(),stateFilter=$('#sourceState').value,region=$('#sourceRegion').value;
  const rows=S.filter(s=>(!q||JSON.stringify(s).toLowerCase().includes(q))&&(!stateFilter||s.state===stateFilter)&&(!region||s.region===region)).sort((a,b)=>a.jurisdiction===PAL?-1:b.jurisdiction===PAL?1:(n(b.loaded_observations)||0)-(n(a.loaded_observations)||0));
  $('#sourceGrid').innerHTML=rows.map(s=>`<article class="source-card ${s.jurisdiction===PAL?'pal-source':''}" data-source-card="${esc(s.source_id)}"><div class="source-card-top"><div><div class="eyebrow">${esc(s.source_id)}</div><h3>${s.jurisdiction===PAL?'★ ':''}${esc(s.name)}</h3></div><span class="status-chip ${esc(s.state||'')}">${s.state==='loaded'?'טעון':s.state==='refreshable'?'ממתין לטעינה':esc(s.state||'')}</span></div><p><b>${esc(jurLabel(s.jurisdiction))}</b> · ${esc(s.region||'')}</p><p>${fmt(s.loaded_observations||0)} observations · ${esc(s.loaded_min_year||'—')}–${esc(s.loaded_max_year||'—')}</p><p>${esc(s.format||'')} · ${esc(s.evidence_tier||'')}</p></article>`).join('')||'<div class="data-gap">לא נמצאו מקורות.</div>';
  $$('[data-source-card]').forEach(c=>c.onclick=()=>renderSourceDetail(c.dataset.sourceCard));
}
function renderSourceDetail(sid){
  const s=sourceById[sid]; if(!s) return; state.selectedSource=sid; const rows=O.filter(r=>r.source_dataset===sid), numericRows=numeric(rows), maps=SM.filter(x=>x.source_dataset===sid), concepts=uniq(maps.map(x=>x.concept_id)), measures=uniq(maps.map(x=>x.measure));
  $('#sourceDetail').classList.remove('hidden');
  $('#sourceDetailHead').innerHTML=`<div class="split-head"><div><div class="eyebrow">${esc(s.source_id)} · ${esc(s.source_family||'')}</div><h2>${s.jurisdiction===PAL?'★ ':''}${esc(s.name)}</h2><p>${esc(s.jurisdiction)} · ${esc(s.institution||'')} · ${esc(s.years_available||'')}</p></div><div class="source-link-row">${s.url?`<a class="secondary" target="_blank" href="${esc(s.url)}">פתיחת המקור ↗</a>`:''}<button id="sourceToData" class="secondary">כל הנתונים בסייר</button></div></div><div class="kpi-grid"><div class="kpi"><strong>${fmt(rows.length)}</strong><span>observations</span></div><div class="kpi"><strong>${fmt(measures.length)}</strong><span>מדדים</span></div><div class="kpi"><strong>${fmt(concepts.length)}</strong><span>מושגים</span></div><div class="kpi"><strong>${rows.length?`${Math.min(...rows.map(r=>n(r.year)).filter(x=>x!==null))}–${Math.max(...rows.map(r=>n(r.year)).filter(x=>x!==null))}`:'—'}</strong><span>כיסוי טעון</span></div><div class="kpi"><strong>${esc(s.state||'')}</strong><span>סטטוס</span></div></div><div class="callout info">${esc(s.message||s.ingest_strategy||'')}</div>`;
  $('#sourceConceptChips').innerHTML=concepts.map(c=>`<button class="measure-chip" data-concept-open="${esc(c)}">${esc(conceptLabel(c))}</button>`).join('')||'<span>טרם נטענו נתונים.</span>';
  $('#sourceMeasure').innerHTML=measures.map(m=>`<option value="${esc(m)}">${esc(measureLabel(m))}</option>`).join('');
  $('#sourceMeasure').disabled=!measures.length; $('#sourceMode').disabled=!measures.length;
  $('#sourceToData').onclick=()=>{ setDataFilters({source_dataset:sid}); nav('data'); };
  $$('[data-concept-open]').forEach(b=>b.onclick=()=>openMeasure(null,b.dataset.conceptOpen));
  $('#sourceMeasure').onchange=renderSourceChart; $('#sourceMode').onchange=renderSourceChart;
  const related=REL.filter(x=>x.source_a===sid||x.source_b===sid);
  $('#relatedSources').innerHTML=related.length?related.map(x=>{const other=x.source_a===sid?x.source_b:x.source_a;return `<div class="related-item"><b>${esc(sourceName(other))}</b><br>${esc(conceptLabel(x.concept_id))} · ${esc(x.relation_type)} · overlap ${esc(x.overlap_years||'ללא')}<br><button class="link-button" data-related-source="${esc(other)}">פתח מקור</button></div>`}).join(''):'<div class="related-item">אין מקור נוסף לאותו מרחב ומושג.</div>';
  $$('[data-related-source]').forEach(b=>b.onclick=()=>renderSourceDetail(b.dataset.relatedSource));
  const coverageYears=uniq(numericRows.map(r=>n(r.year))).sort((a,b)=>a-b), z=measures.map(m=>coverageYears.map(y=>numericRows.filter(r=>r.measure===m&&n(r.year)===y).length));
  if(measures.length&&coverageYears.length) safeHeatmap('sourceCoverage',coverageYears,measures.map(measureLabel),z,{margin:{l:170,r:10,t:10,b:42}},'%{y}<br>%{x}: %{z}<extra></extra>'); else chartGap('sourceCoverage','למקור זה טרם נטענו observations.');
  state.sourceRows=rows; renderSourceDataTable(); renderSourceChart();
}
function renderSourceChart(){
  const sid=state.selectedSource,m=$('#sourceMeasure').value,mode=$('#sourceMode').value; if(!sid||!m){ chartGap('sourceChart','בחרו מקור טעון ומדד.'); return; }
  const rows=numeric(O).filter(r=>r.source_dataset===sid&&r.measure===m), pts=points(rows,r=>r.facility_name||r.geography_name||jurLabel(r.jurisdiction)); const years=pts.map(p=>p.x),y0=Math.min(...years),y1=Math.max(...years);
  renderSeries('sourceChart',pts,mode,y0,y1,{yaxis:{title:uniq(rows.map(r=>r.unit)).join('/')}},{title:`${sourceName(sid)} — ${measureLabel(m)}`});
}
function renderSourceDataTable(){
  const rows=state.sourceRows.slice(0,500); $('#sourceDataTable').innerHTML=tableHtml(['שנה','מרחב/מוסד','מושג','מדד','ערך','Grade','פרטים'],rows.map(r=>[r.year||'',esc(r.facility_name||r.geography_name||r.jurisdiction),esc(r.concept_label_he||''),esc(measureLabel(r.measure)),`${fmt(r.value)} ${esc(r.unit||'')}`,esc(r.comparability_grade||''),`<button class="detail-button" data-source-obs="${esc(r.observation_id)}">פתח</button>`]));
  $$('[data-source-obs]').forEach(b=>b.onclick=()=>showObservationDrawer([b.dataset.sourceObs],'Observation מן המקור'));
}
function openMeasure(measure=null,concept=null){ nav('atlas'); activateAtlasTab('measures'); if(concept) $('#measureConcept').value=concept; fillMeasureSelect(); if(measure) $('#measureSelect').value=measure; renderMeasureAtlas(); }
function fillMeasureSelect(){
  const c=$('#measureConcept').value, measures=MR.filter(m=>!c||m.concept_id===c).sort((a,b)=>a.label_he.localeCompare(b.label_he,'he')); $('#measureSelect').innerHTML=measures.map(m=>`<option value="${esc(m.measure)}">${esc(m.label_he)}</option>`).join('');
}
function renderMeasureAtlas(){
  const m=$('#measureSelect').value,mode=$('#measureMode').value,y0=n($('#measureY0').value),y1=n($('#measureY1').value),meta=measureById[m]||{}; if(!m) return;
  const rows=numeric(O).filter(r=>r.measure===m&&n(r.year)>=y0&&n(r.year)<=y1), pts=points(rows,r=>jurLabel(r.jurisdiction));
  $('#measureChartTitle').textContent=`${measureLabel(m)} — כל המרחבים`;
  $('#measureDescription').innerHTML=`<b>${esc(meta.label_he||m)}</b> · מושג: ${esc(conceptLabel(meta.concept_id))} · בסיס זמן: ${esc(meta.time_basis||'')} · aggregation: ${esc(meta.aggregation_default||'')} · השוואה בין מרחבים: ${meta.comparable_across_jurisdictions?'כן, בכפוף ל־Grade וליחידה':'לא כברירת מחדל'}`;
  renderSeries('measureChart',pts,mode,y0,y1,{yaxis:{title:uniq(rows.map(r=>r.unit)).join(' / ')}},{title:`אטלס מדד: ${m}`});
  const avg=transformPoints(pts,'periodavg',y0,y1).sort((a,b)=>b.y-a.y).slice(0,30); safePlot('measureRanking',avg,{xaxis:{tickangle:-35}},{type:'bar',title:'דירוג מרחבים'});
  const sources=uniq(rows.map(r=>r.source_dataset)), years=[]; for(let y=y0;y<=y1;y++) years.push(y); const z=sources.map(sid=>years.map(y=>rows.filter(r=>r.source_dataset===sid&&n(r.year)===y).length)); safeHeatmap('measureCoverage',years,sources.map(sourceName),z,{margin:{l:185,r:10,t:10,b:40}},'%{y}<br>%{x}: %{z}<extra></extra>');
  const maps=SM.filter(x=>x.measure===m); $('#measureSourceTable').innerHTML=tableHtml(['מקור','מרחב','observations','שנים','יחידות','Grades','הגדרה מאומתת','קישור'],maps.map(x=>[esc(sourceName(x.source_dataset)),esc(x.jurisdictions),fmt(x.observations),`${esc(x.min_year)}–${esc(x.max_year)}`,esc(x.units),esc(x.grades),`${fmt(x.definition_verified_pct)}%`,`<button class="link-button" data-msource="${esc(x.source_dataset)}">פתח מקור</button>`])); $$('[data-msource]').forEach(b=>b.onclick=()=>openSource(b.dataset.msource));
}
function activateAtlasTab(tab){ state.atlasTab=tab; $$('#atlasTabs .subnav-button').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab)); $$('[data-atlas-panel]').forEach(p=>p.classList.toggle('active',p.dataset.atlasPanel===tab)); if(tab==='sources') renderSourceCards(); if(tab==='measures') renderMeasureAtlas(); if(tab==='network') renderNetwork(); }
function renderNetwork(){
  const region=$('#networkRegion').value,concept=$('#networkConcept').value,showRefresh=$('#networkRefreshable').checked;
  let sources=S.filter(s=>(!region||s.region===region)&&(showRefresh||n(s.loaded_observations)>0));
  if(concept) sources=sources.filter(s=>COV.find(c=>c.source_id===s.source_id)?.[concept]);
  const sourceIds=new Set(sources.map(s=>s.source_id)); const concepts=(concept?[concept]:uniq(SM.filter(x=>sourceIds.has(x.source_dataset)).map(x=>x.concept_id))).filter(Boolean);
  const nodePos={}, nodes=[]; const r1=1,r2=2.15;
  concepts.forEach((c,i)=>{const a=2*Math.PI*i/Math.max(concepts.length,1);nodePos['c:'+c]=[r1*Math.cos(a),r1*Math.sin(a)];nodes.push({id:'c:'+c,label:conceptLabel(c),kind:'concept',x:nodePos['c:'+c][0],y:nodePos['c:'+c][1],ref:c});});
  sources.forEach((s,i)=>{const a=2*Math.PI*i/Math.max(sources.length,1);nodePos['s:'+s.source_id]=[r2*Math.cos(a),r2*Math.sin(a)];nodes.push({id:'s:'+s.source_id,label:s.jurisdiction===PAL?'★ פלסטין — '+s.name:s.name,kind:'source',x:nodePos['s:'+s.source_id][0],y:nodePos['s:'+s.source_id][1],ref:s.source_id,state:s.state});});
  const edgeX=[],edgeY=[]; for(const x of SM){ if(!sourceIds.has(x.source_dataset)||!concepts.includes(x.concept_id)) continue; const a=nodePos['s:'+x.source_dataset],b=nodePos['c:'+x.concept_id]; if(a&&b){edgeX.push(a[0],b[0],null);edgeY.push(a[1],b[1],null);} }
  try{
    const traces=[{type:'scatter',mode:'lines',x:edgeX,y:edgeY,line:{color:'#cad3cf',width:1},hoverinfo:'skip',showlegend:false},{type:'scatter',mode:'markers+text',x:nodes.map(x=>x.x),y:nodes.map(x=>x.y),text:nodes.map(x=>x.kind==='concept'?x.label:''),textposition:'middle center',marker:{size:nodes.map(x=>x.kind==='concept'?42:(x.state==='loaded'?17:12)),color:nodes.map(x=>x.kind==='concept'?'#315f4d':x.ref==='PAL_V2'?PAL_COLOR:x.state==='loaded'?'#527289':'#c5aaa0'),line:{color:'#fff',width:1}},customdata:nodes.map(x=>JSON.stringify(x)),hovertext:nodes.map(x=>`${x.label}<br>${x.kind==='concept'?'מושג':'מקור'}`),hovertemplate:'%{hovertext}<extra></extra>',showlegend:false}];
    Plotly.react('sourceNetwork',traces,{paper_bgcolor:'transparent',plot_bgcolor:'transparent',margin:{l:10,r:10,t:10,b:10},xaxis:{visible:false,fixedrange:true},yaxis:{visible:false,fixedrange:true,scaleanchor:'x'}},plotCfg);
    const el=$('#sourceNetwork'); try{el.removeAllListeners?.('plotly_click')}catch(_){ } el.on('plotly_click',ev=>{try{const d=JSON.parse(ev.points[0].customdata); if(d.kind==='source')openSource(d.ref);else openMeasure(null,d.ref);}catch(_){}});
    $('#meta-sourceNetwork').innerHTML=`<span class="meta-pill">${sources.length} מקורות</span><span class="meta-pill">${concepts.length} מושגים</span><span class="meta-pill">לחצו על node לניווט</span>`; chartHealth.sourceNetwork={status:'ok',message:'network rendered',count:nodes.length};
  }catch(e){chartError('sourceNetwork',e.message||String(e));}
}

function fillMapMeasures(){ const c=$('#mapConcept').value, measures=MR.filter(m=>m.concept_id===c && O.some(r=>r.measure===m.measure)); $('#mapMeasure').innerHTML=`<option value="__aligned__">סדרה מיושרת לפי המושג — כוללת את פלסטין כשאפשר</option>`+measures.map(m=>`<option value="${esc(m.measure)}">${esc(m.label_he)} · ${esc(m.time_basis)}</option>`).join(''); }
function mapRows(){
  const concept=$('#mapConcept').value,m=$('#mapMeasure').value,mode=$('#mapMode').value; let rows=[];
  const alignedForPeriod=(y0,y1)=>{
    const all=[];
    for(const jur of uniq(O.map(r=>r.jurisdiction))) all.push(...comparisonCandidates(jur,concept,m,'system',y0,y1));
    return all;
  };
  const label=m==='__aligned__'?`${conceptLabel(concept)} — סדרה מיושרת`:measureLabel(m);
  if(mode==='year'){
    const y=n($('#mapYear').value);
    rows=alignedForPeriod(y,y);
    $('#mapQuestion').textContent=`${y}: היכן דווח ${label}? פלסטין מודגשת ונכללת כאשר יש observation מקביל.`;
  } else {
    const y0=n($('#mapY0').value),y1=n($('#mapY1').value),all=alignedForPeriod(y0,y1),g=groupBy(all,r=>r.jurisdiction);
    rows=Object.entries(g).map(([jur,rr])=>{const b=bestObservation(rr);return {...b,value:mean(rr.map(valueOf)),year:`${y0}–${y1}`,observation_id:rr.map(r=>r.observation_id).join('|'),_rows:rr};});
    $('#mapQuestion').textContent=`${y0}–${y1}: ממוצע רב־שנתי של ${label} לפי מרחב.`;
  }
  return rows.filter(r=>jurByName[r.jurisdiction]&&n(jurByName[r.jurisdiction].latitude)!==null);
}
function renderMap(){
  const rows=mapRows(); if(!rows.length){chartGap('worldMap','אין נתונים למפה בבחירה זו.');chartGap('mapRanking','אין נתונים לדירוג.');return;}
  const pts=rows.map(r=>{const rr=r._rows||[r];return {x:r.jurisdiction,y:valueOf(r),name:jurLabel(r.jurisdiction),ids:rr.flatMap(x=>String(x.observation_id).split('|')),rows:rr,unit:r.unit||'',grade:r.comparability_grade||'B',formula:r._rows?`ממוצע של ${rr.length} observations`:''};});
  const max=Math.max(...pts.map(p=>p.y),1), lons=rows.map(r=>n(jurByName[r.jurisdiction].longitude)),lats=rows.map(r=>n(jurByName[r.jurisdiction].latitude));
  try{
    Plotly.react('worldMap',[{type:'scatter',x:WORLD.lon,y:WORLD.lat,mode:'lines',line:{color:'#c5cdc9',width:1},hoverinfo:'skip',showlegend:false},{type:'scatter',x:lons,y:lats,mode:'markers+text',text:rows.map(r=>r.jurisdiction===PAL?'★ פלסטין':''),textposition:'top center',marker:{size:pts.map(p=>12+30*Math.sqrt(p.y/max)),color:rows.map(r=>r.jurisdiction===PAL?PAL_COLOR:'#477862'),line:{color:'#fff',width:1}},customdata:pts.map(p=>JSON.stringify({ids:p.ids,formula:p.formula,title:p.name})),hovertext:pts.map(p=>`${p.name}<br>${fmt(p.y)} ${esc(p.unit)}`),hovertemplate:'%{hovertext}<br>לחצו למקור<extra></extra>',showlegend:false}],{paper_bgcolor:'transparent',plot_bgcolor:'#f7f6f1',margin:{l:5,r:5,t:5,b:5},xaxis:{visible:false,range:[-180,180],fixedrange:true},yaxis:{visible:false,range:[-60,82],fixedrange:true}},plotCfg); bindPlotClick('worldMap','מפת מרחבים'); chartMeta('worldMap',pts,$('#mapMode').value==='year'?'annual':'periodavg'); sourceFooter('worldMap',pts); chartHealth.worldMap={status:'ok',message:`${rows.length} map points`,count:rows.length};
  }catch(e){chartError('worldMap',e.message||String(e));}
  const rank=[...pts].sort((a,b)=>b.y-a.y); safePlot('mapRanking',rank,{xaxis:{tickangle:-35}},{type:'bar',title:'דירוג מפה'});
  const density=JREG.filter(j=>n(j.loaded_observations)>0).map(j=>({x:j.jurisdiction,y:n(j.loaded_observations),name:jurLabel(j.jurisdiction),ids:[],rows:[],unit:'observations'})).sort((a,b)=>b.y-a.y).slice(0,25); safePlot('mapDensity',density,{xaxis:{tickangle:-35},yaxis:{title:'observations'}},{type:'bar',title:'צפיפות נתונים'});
}
function renderFacilityMap(){
  const m=$('#facilityMapMeasure').value,y=n($('#facilityMapYear').value),rows=preferRows(numeric(O).filter(r=>r.jurisdiction===PAL&&r.measure===m&&r.geography_level==='facility'&&n(r.year)===y)).filter(r=>{const f=FC.find(x=>x.facility_name===r.facility_name);return f&&n(f.latitude)!==null;});
  if(!rows.length){chartGap('palFacilityMap','אין נתונים מוסדיים עם קואורדינטות בשנה ובמדד שנבחרו.');return;}
  const max=Math.max(...rows.map(valueOf),1),pts=rows.map(r=>point(r,r.facility_name));
  try{Plotly.react('palFacilityMap',[{type:'scatter',x:rows.map(r=>n(FC.find(x=>x.facility_name===r.facility_name).longitude)),y:rows.map(r=>n(FC.find(x=>x.facility_name===r.facility_name).latitude)),mode:'markers+text',text:rows.map(r=>r.facility_name),textposition:'top center',marker:{size:rows.map(r=>10+32*Math.sqrt(valueOf(r)/max)),color:rows.map(r=>r.facility_type?.includes('detention')?'#934f55':r.facility_type?.includes('lockup')?'#527289':PAL_COLOR),line:{color:'#fff',width:1}},customdata:pts.map(p=>JSON.stringify({ids:p.ids,title:p.name})),hovertext:rows.map(r=>`${r.facility_name}<br>${fmt(r.value)} ${r.unit||''}`),hovertemplate:'%{hovertext}<extra></extra>',showlegend:false}],{paper_bgcolor:'transparent',plot_bgcolor:'#f7f6f1',margin:{l:40,r:15,t:10,b:35},xaxis:{title:'Longitude',range:[34.6,35.7]},yaxis:{title:'Latitude',range:[31.0,33.1]}},plotCfg);bindPlotClick('palFacilityMap','מפת מוסדות בפלסטין');chartMeta('palFacilityMap',pts,'annual',`${y}`);sourceFooter('palFacilityMap',pts);chartHealth.palFacilityMap={status:'ok',message:`${rows.length} facilities`,count:rows.length};}catch(e){chartError('palFacilityMap',e.message||String(e));}
}
function renderGlobalCoverage(){
  const rows=numeric(O),jurs=uniq(rows.map(r=>r.jurisdiction)).sort((a,b)=>a===PAL?-1:b===PAL?1:a.localeCompare(b)),years=[];const minYear=n(META.min_year)??1900,maxYear=n(META.max_year)??1950;for(let y=minYear;y<=maxYear;y++)years.push(y);const z=jurs.map(j=>years.map(y=>rows.filter(r=>r.jurisdiction===j&&n(r.year)===y).length));safeHeatmap('globalCoverage',years,jurs.map(jurLabel),z,{margin:{l:180,r:10,t:10,b:45},yaxis:{automargin:true},xaxis:{dtick:5}},'%{y}<br>%{x}: %{z} observations<extra></extra>');
}

function setDataFilters(f={}){
  if(f.source_dataset!==undefined) $('#dataSource').value=f.source_dataset||'';
  if(f.jurisdiction!==undefined) $('#dataJurisdiction').value=f.jurisdiction||'';
  if(f.concept_id!==undefined) $('#dataConcept').value=f.concept_id||'';
  if(f.measure!==undefined) $('#dataMeasure').value=f.measure||'';
  if(f.year!==undefined){$('#dataY0').value=f.year;$('#dataY1').value=f.year;}
  state.dataPage=0;
}
function dataFilteredRows(){
  const q=String($('#dataSearch').value||'').toLowerCase(),y0=n($('#dataY0').value),y1=n($('#dataY1').value);
  return O.filter(r=>(!$('#dataSource').value||r.source_dataset===$('#dataSource').value)&&(!$('#dataJurisdiction').value||r.jurisdiction===$('#dataJurisdiction').value)&&(!$('#dataConcept').value||r.concept_id===$('#dataConcept').value)&&(!$('#dataMeasure').value||r.measure===$('#dataMeasure').value)&&(!$('#dataTimeBasis').value||r.time_basis===$('#dataTimeBasis').value)&&(!$('#dataGrade').value||r.comparability_grade===$('#dataGrade').value)&&(!$('#dataGeo').value||r.geography_level===$('#dataGeo').value)&&(n(r.year)===null||(n(r.year)>=y0&&n(r.year)<=y1))&&(!q||JSON.stringify(r).toLowerCase().includes(q)));
}
function renderData(){
  const rows=dataFilteredRows();state.dataRows=rows;const pages=Math.max(1,Math.ceil(rows.length/state.dataPageSize));state.dataPage=Math.max(0,Math.min(state.dataPage,pages-1));const page=rows.slice(state.dataPage*state.dataPageSize,(state.dataPage+1)*state.dataPageSize);$('#dataCount').textContent=`${rows.length.toLocaleString()} observations`;$('#dataPage').textContent=`${state.dataPage+1} / ${pages}`;
  $('#dataTable').innerHTML=tableHtml(['שנה','מרחב','מקור','רמה/מוסד','מושג','מדד','ערך','Grade','פרטים'],page.map(r=>[r.year||'',esc(jurLabel(r.jurisdiction)),`<button class="link-button" data-row-source="${esc(r.source_dataset)}">${esc(sourceName(r.source_dataset))}</button>`,esc(r.facility_name||r.geography_name||r.geography_level),`<button class="link-button" data-row-measure="${esc(r.measure)}">${esc(r.concept_label_he||conceptLabel(r.concept_id))}</button>`,esc(measureLabel(r.measure)),`${fmt(r.value)} ${esc(r.unit||'')}`,esc(r.comparability_grade||''),`<button class="detail-button" data-row-obs="${esc(r.observation_id)}">פתח</button>`]));
  $$('[data-row-obs]').forEach(b=>b.onclick=()=>showObservationDrawer([b.dataset.rowObs],'Observation'));$$('[data-row-source]').forEach(b=>b.onclick=()=>openSource(b.dataset.rowSource));$$('[data-row-measure]').forEach(b=>b.onclick=()=>openMeasure(b.dataset.rowMeasure));
}
function renderDataSummary(){
  const rows=state.dataRows,dim=$('#summaryDimension').value,agg=$('#summaryAggregation').value,g=groupBy(rows,r=>String(r[dim]??'לא ידוע')),pts=[];
  for(const [name,rr] of Object.entries(g)){const vals=rr.map(valueOf).filter(x=>x!==null);let y=agg==='count'?rr.length:agg==='sum'?sum(vals):mean(vals);if(y!==null)pts.push({x:name,y,name,ids:rr.slice(0,50).map(r=>r.observation_id),rows:rr.slice(0,200),unit:agg,grade:'',formula:`${agg} של ${rr.length} observations`});}
  pts.sort((a,b)=>b.y-a.y);safePlot('dataSummaryChart',pts.slice(0,40),{xaxis:{tickangle:-35},yaxis:{title:agg}},{type:'bar',title:'סיכום נתונים'});
}

function renderQuality(){
  const provComplete=O.filter(r=>r.source_url&&r.source_locator&&r.source_record_id&&r.transformation).length,loaded=S.filter(s=>n(s.loaded_observations)>0).length,refresh=S.length-loaded,unmapped=O.filter(r=>!r.concept_id).length,conflicts=EQ.filter(x=>x.agreement_status==='conflict').length;
  $('#qualityKpis').innerHTML=[['Observations',O.length],['מקורות טעונים',loaded],['מקורות ממתינים',refresh],['Provenance מלא',`${provComplete}/${O.length}`],['סתירות מדויקות',conflicts]].map(([l,v])=>`<div class="kpi"><strong>${esc(v)}</strong><span>${esc(l)}</span></div>`).join('');
  $('#syncAudit').innerHTML=SYNC.map(x=>`<div class="audit-item ${esc(x.severity)}"><b>${esc(x.check)}</b><p>${esc(x.message)}</p><span>${fmt(x.count)}</span></div>`).join('');
  const grades=groupBy(O,r=>r.comparability_grade||'U'),gpts=Object.entries(grades).map(([name,rr])=>({x:name,y:rr.length,name,ids:[],rows:[],unit:'observations'}));safePlot('gradeChart',gpts,{yaxis:{title:'observations'}},{type:'bar',title:'Grades'});
  const concepts=CR.map(c=>c.concept_id),sources=S.map(s=>s.source_id),z=sources.map(sid=>concepts.map(c=>n(COV.find(x=>x.source_id===sid)?.[c])||0));safeHeatmap('sourceConceptHeatmap',concepts.map(conceptLabel),sources.map(sourceName),z,{margin:{l:220,r:10,t:10,b:140},xaxis:{tickangle:-35},yaxis:{automargin:true}},'%{y}<br>%{x}: %{z}<extra></extra>');
  $('#qaList').innerHTML=Q.map(x=>`<div class="audit-item ${esc(x.severity||'warning')}"><b>${esc(x.jurisdiction||x.source||'')} · ${esc(x.year||'')} · ${esc(x.check||'QA')}</b><p>${esc(x.message||'')}</p><span>${esc(x.observed??'')}</span></div>`).join('')||'<div class="audit-item pass">אין ממצאי QA.</div>';
  $('#refreshableList').innerHTML=S.filter(s=>n(s.loaded_observations)===0).map(s=>`<div class="audit-item warning"><b>${esc(s.name)}</b><p>${esc(s.status||s.message||'')}</p><button class="link-button" data-refresh-source="${esc(s.source_id)}">פתח באטלס</button>${s.url?` · <a target="_blank" href="${esc(s.url)}">מקור חיצוני ↗</a>`:''}</div>`).join('')||'<div class="audit-item pass">כל המקורות טעונים.</div>';$$('[data-refresh-source]').forEach(b=>b.onclick=()=>openSource(b.dataset.refreshSource));
  $('#equivalenceTable').innerHTML=tableHtml(['מרחב','שנה','מדד','מקורות','spread','סטטוס'],EQ.slice(0,200).map(x=>[esc(x.jurisdiction),esc(x.year),esc(measureLabel(x.measure)),esc(x.sources),fmt(x.absolute_spread),esc(x.agreement_status)]));renderChartHealth();
}
function renderChartHealth(){
  const el=$('#chartHealth');if(!el)return;const rows=Object.entries(chartHealth);el.innerHTML=rows.length?rows.map(([id,x])=>`<div class="health-item ${esc(x.status)}"><b>${esc(id)}</b><br><span>${esc(x.status)} · ${esc(x.message||'')}</span></div>`).join(''):'<div class="audit-item info">הגרפים יירשמו כאן לאחר פתיחת המסכים.</div>';
}
function renderDownloads(){
  const files=[
    ['observations.csv',`כל ${O.length.toLocaleString()} ה־observations`],['source_registry.csv',`כל ${S.length} המקורות, טעונים וממתינים`],['measure_registry.csv',`מיפוי ${MR.length} המדדים`],['concept_registry.csv',`מילון ${CR.length} המושגים`],['source_measure_map.csv','כל צמדי מקור × מדד'],['source_concept_coverage.csv','כיסוי מקור × מושג'],['source_relationships.csv','קשרים בין מקורות'],['observation_equivalence_groups.csv','חלופות מדויקות בלבד'],['jurisdiction_registry.csv','מרחבים וקואורדינטות'],['facility_crosswalk.csv','מוסדות פלסטין'],['synchronisation_audit.csv','בדיקות סנכרון'],['quality_audit.csv','ממצאי QA'],['provenance_audit.csv','ביקורת provenance ברמת observation'],['source_verification_audit.csv','סיכום אימות לפי מקור'],['variable_crosswalk.csv','Crosswalk משתנים'],['palestine_data_dictionary.csv','מילון פלסטין'],['canonical_schema.csv','הסכמה הקנונית'],['SOURCE_MAPPING_V7.md','תיעוד מלא של מיפוי המקורות והמדדים'],['SYSTEM_QA_V7.md','דוח איכות ובדיקת דפדפן'],['browser_qa_v7.json','תוצאות runtime לכל מסך ולשונית'],['DATA_SOURCES.md','קטלוג כל המקורות'],['README_HE.md','הוראות שימוש בעברית']
  ];
  $('#downloadGrid').innerHTML=files.map(([f,d])=>`<a class="download-card" href="downloads/${encodeURIComponent(f)}" download><b>${esc(f)}</b><span>${esc(d)}</span><strong>הורדה ↓</strong></a>`).join('');
}
function tableHtml(headers,rows){ return `<thead><tr>${headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${c??''}</td>`).join('')}</tr>`).join('')}</tbody>`; }
function fillSelect(el,items,{all=false,label=x=>x,value=x=>x}={}){ if(!el)return;el.innerHTML=(all?'<option value="">הכול</option>':'')+items.map(x=>`<option value="${esc(value(x))}">${esc(label(x))}</option>`).join(''); }

function nav(view,push=true){
  state.activeView=view;$$('.view').forEach(v=>v.classList.toggle('active',v.id===`view-${view}`));$$('.nav').forEach(b=>b.classList.toggle('active',b.dataset.view===view));$('#sidebar').classList.remove('open');
  if(push) history.replaceState(null,'',`#${view}`);
  if(view==='palestine')renderPalestine();if(view==='compare')renderCompare();if(view==='atlas')activateAtlasTab(state.atlasTab);if(view==='map'){renderMap();renderFacilityMap();renderGlobalCoverage();}if(view==='data')renderData();if(view==='quality')renderQuality();if(view==='downloads')renderDownloads();window.scrollTo({top:0,behavior:'instant'});
}
function initSelections(){
  const years=numeric(O).map(r=>n(r.year)),minY=Math.min(...years),maxY=Math.max(...years),pal=numeric(O).filter(r=>r.jurisdiction===PAL);
  $('#buildBadge').textContent=`${O.length.toLocaleString()} obs · ${O.filter(r=>r.source_dataset).length?uniq(O.map(r=>r.source_dataset)).length:0}/${S.length} מקורות`;
  $('#palHeroStats').innerHTML=[[pal.length,'observations'],[uniq(pal.map(r=>r.measure)).length,'מדדים'],[uniq(pal.map(r=>r.facility_name)).length,'מוסדות'],[`${Math.min(...pal.map(r=>n(r.year)))}–${Math.max(...pal.map(r=>n(r.year)))}`,'כיסוי']].map(([v,l])=>`<div class="mini-stat"><strong>${esc(v)}</strong><span>${esc(l)}</span></div>`).join('');
  $('#atlasStats').innerHTML=[[S.length,'מקורות רשומים'],[uniq(O.map(r=>r.source_dataset)).length,'מקורות טעונים'],[MR.length,'מדדים'],[CR.length,'מושגים']].map(([v,l])=>`<div class="mini-stat"><strong>${esc(v)}</strong><span>${esc(l)}</span></div>`).join('');
  $('#palY0').value=1920;$('#palY1').value=1948;$('#cmpY0').value=1920;$('#cmpY1').value=1948;$('#measureY0').value=minY;$('#measureY1').value=maxY;$('#mapYear').value=1938;$('#mapY0').value=1930;$('#mapY1').value=1944;$('#facilityMapYear').value=1938;$('#dataY0').value=minY;$('#dataY1').value=maxY;
  const compareConcepts=CR.filter(c=>O.some(r=>r.concept_id===c.concept_id&&r.jurisdiction===PAL));fillSelect($('#cmpConcept'),compareConcepts,{label:x=>x.concept_label_he,value:x=>x.concept_id});$('#cmpConcept').value='custodial_population_total';fillCompareMeasures();
  $('#cmpJurisdictions').innerHTML=uniq(O.map(r=>r.jurisdiction)).sort((a,b)=>a===PAL?-1:b===PAL?1:a.localeCompare(b)).map(j=>`<label class="${j===PAL?'pal-fixed':''}"><input type="checkbox" value="${esc(j)}" ${[PAL,'New Zealand','Canada','Ceylon','Jamaica','British Nigeria','Kenya','Hong Kong'].includes(j)?'checked':''} ${j===PAL?'disabled':''}><span>${esc(jurLabel(j))}</span></label>`).join('');
  fillSelect($('#sourceRegion'),uniq(S.map(s=>s.region)).sort(),{all:true});fillSelect($('#networkRegion'),uniq(S.map(s=>s.region)).sort(),{all:true});fillSelect($('#networkConcept'),CR,{all:true,label:x=>x.concept_label_he,value:x=>x.concept_id});
  fillSelect($('#measureConcept'),CR,{label:x=>x.concept_label_he,value:x=>x.concept_id});$('#measureConcept').value='custodial_population_total';fillMeasureSelect();$('#measureSelect').value='stock_eoy_total';
  fillSelect($('#mapConcept'),CR.filter(c=>MR.some(m=>m.concept_id===c.concept_id&&m.comparable_across_jurisdictions)),{label:x=>x.concept_label_he,value:x=>x.concept_id});$('#mapConcept').value='custodial_population_total';fillMapMeasures();$('#mapMeasure').value='__aligned__';
  const facMeasures=uniq(O.filter(r=>r.jurisdiction===PAL&&r.geography_level==='facility'&&valueOf(r)!==null).map(r=>r.measure)).sort((a,b)=>measureLabel(a).localeCompare(measureLabel(b),'he'));fillSelect($('#facilityMapMeasure'),facMeasures,{label:measureLabel});$('#facilityMapMeasure').value='stock_eoy_total';
  fillSelect($('#dataSource'),S,{all:true,label:x=>sourceName(x.source_id),value:x=>x.source_id});fillSelect($('#dataJurisdiction'),uniq(O.map(r=>r.jurisdiction)).sort(),{all:true});fillSelect($('#dataConcept'),CR,{all:true,label:x=>x.concept_label_he,value:x=>x.concept_id});fillSelect($('#dataMeasure'),MR,{all:true,label:x=>x.label_he,value:x=>x.measure});fillSelect($('#dataTimeBasis'),uniq(O.map(r=>r.time_basis)).sort(),{all:true});fillSelect($('#dataGrade'),uniq(O.map(r=>r.comparability_grade)).sort(),{all:true});fillSelect($('#dataGeo'),uniq(O.map(r=>r.geography_level)).sort(),{all:true});
}
function bindEvents(){
  $$('.nav').forEach(b=>b.onclick=()=>nav(b.dataset.view));$('#mobileMenu').onclick=()=>$('#sidebar').classList.toggle('open');$$('[data-go]').forEach(x=>x.onclick=()=>nav(x.dataset.go));
  $$('#palTabs .subnav-button').forEach(b=>b.onclick=()=>{state.palTab=b.dataset.tab;$$('#palTabs .subnav-button').forEach(x=>x.classList.toggle('active',x===b));$$('[data-panel]').forEach(p=>p.classList.toggle('active',p.dataset.panel===state.palTab));renderPalestine();});
  $$('#palPresets button').forEach(b=>b.onclick=()=>{if(b.dataset.period==='full'){$('#palY0').value=1920;$('#palY1').value=1948;}else{const [a,z]=b.dataset.period.split(',');$('#palY0').value=a;$('#palY1').value=z;}renderPalestine();});$('#applyPal').onclick=renderPalestine;$('#palMode').onchange=renderPalestine;
  $('#cmpConcept').onchange=()=>{fillCompareMeasures();renderCompare();};$('#cmpMeasure').onchange=renderCompare;$('#runCompare').onclick=renderCompare;$('#downloadCompare').onclick=()=>downloadRows(state.compareRows,'comparison_underlying_observations.csv');
  $$('#atlasTabs .subnav-button').forEach(b=>b.onclick=()=>activateAtlasTab(b.dataset.tab));$('#sourceSearch').oninput=renderSourceCards;$('#sourceState').onchange=renderSourceCards;$('#sourceRegion').onchange=renderSourceCards;$('#measureConcept').onchange=()=>{fillMeasureSelect();renderMeasureAtlas();};$('#runMeasure').onclick=renderMeasureAtlas;$('#runNetwork').onclick=renderNetwork;
  $('#mapConcept').onchange=()=>{fillMapMeasures();renderMap();};$('#mapMode').onchange=()=>{$$('.map-year-control').forEach(x=>x.classList.toggle('hidden',$('#mapMode').value!=='year'));$$('.map-period-control').forEach(x=>x.classList.toggle('hidden',$('#mapMode').value!=='period'));};$('#runMap').onclick=renderMap;$('#runFacilityMap').onclick=renderFacilityMap;
  ['dataSource','dataJurisdiction','dataConcept','dataMeasure','dataTimeBasis','dataGrade','dataGeo','dataY0','dataY1'].forEach(id=>$('#'+id).onchange=()=>{state.dataPage=0;renderData();});$('#dataSearch').oninput=()=>{state.dataPage=0;renderData();};$('#dataPrev').onclick=()=>{state.dataPage=Math.max(0,state.dataPage-1);renderData();};$('#dataNext').onclick=()=>{state.dataPage++;renderData();};$('#resetData').onclick=()=>{['dataSource','dataJurisdiction','dataConcept','dataMeasure','dataTimeBasis','dataGrade','dataGeo'].forEach(id=>$('#'+id).value='');$('#dataSearch').value='';$('#dataY0').value=META.min_year;$('#dataY1').value=META.max_year;state.dataPage=0;renderData();};$('#downloadFiltered').onclick=()=>downloadRows(state.dataRows,'filtered_observations.csv');$('#runSummary').onclick=renderDataSummary;
  $('#closeDrawer').onclick=closeDrawer;$('#drawerBackdrop').onclick=closeDrawer;
}
function init(){
  initSelections();bindEvents();const hash=location.hash.replace('#','');nav(['palestine','compare','atlas','map','data','quality','downloads'].includes(hash)?hash:'palestine',false);
}

init();
})();
