(()=>{'use strict';
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const views={palestine:'פלסטין',compare:'השוואה',atlas:'אטלס מקורות',map:'מפה',data:'נתונים',quality:'איכות וקישוריות',downloads:'הורדות'};
const searchOverlay=$('#searchOverlay'), searchInput=$('#globalSearchInput'),searchResults=$('#globalSearchResults'),helpOverlay=$('#helpOverlay');
let entries=[];let filtered=[];
function buildIndex(){entries=[];$$('#sidebar [data-view]').forEach(b=>entries.push({label:b.querySelector('b')?.textContent||'',hint:'מסך ראשי',view:b.dataset.view}));
$$('#view-palestine .chart-card').forEach(card=>{const label=card.querySelector('h3')?.textContent||'';const chart=card.querySelector('.chart');const panel=card.closest('[data-panel]'); if(label&&chart) entries.push({label,hint:'פלסטין · גרף',view:'palestine',tab:panel?.dataset.panel,anchor:chart.id})});
$$('#view-palestine .subnav-button').forEach(b=>entries.push({label:b.textContent,hint:'פלסטין · נושא',view:'palestine',tab:b.dataset.tab}));
$$('.view:not(#view-palestine) h3').forEach(h=>{const v=h.closest('.view');if(!v)return;entries.push({label:h.textContent,hint:views[v.id.replace('view-','')]||'מסך',view:v.id.replace('view-',''),anchor:h.closest('article')?.querySelector('.chart')?.id})});}
function jump(e){const btn=$(`#sidebar [data-view="${e.view}"]`);btn?.click();if(e.tab){const tab=$(`#palTabs [data-tab="${e.tab}"]`);tab?.click();}hideSearch();if(e.anchor){requestAnimationFrame(()=>setTimeout(()=>document.getElementById(e.anchor)?.closest('.card')?.scrollIntoView({block:'center',behavior:'smooth'}),140));}}
function paint(){const q=searchInput.value.toLowerCase().trim();filtered=entries.filter(e=>!q||`${e.label} ${e.hint}`.toLowerCase().includes(q)).slice(0,20);searchResults.innerHTML=filtered.length?filtered.map((e,i)=>`<button type="button" class="search-result" data-search-i="${i}"><span><b>${e.label.replace(/&/g,'&amp;').replace(/</g,'&lt;')}</b><small>${e.hint}</small></span><span aria-hidden="true">↖</span></button>`).join(''):'<div class="search-empty">אין תוצאות. אפשר לחפש לפי נושא, שנה, סוג נתון או שם גרף.</div>';searchResults.querySelectorAll('[data-search-i]').forEach(b=>b.addEventListener('click',()=>jump(filtered[Number(b.dataset.searchI)])));}
function showSearch(){helpOverlay.classList.add('hidden');searchOverlay.classList.remove('hidden');searchInput.value='';paint();searchInput.focus();}
function hideSearch(){searchOverlay.classList.add('hidden');}
function showHelp(){hideSearch();helpOverlay.classList.remove('hidden');}
function closeHelp(){helpOverlay.classList.add('hidden');}
$('#globalSearchOpen').onclick=showSearch;$('#globalSearchClose').onclick=hideSearch;$('#helpOpen').onclick=showHelp;$('#helpClose').onclick=closeHelp;$('#helpStart').onclick=()=>{closeHelp();$('#sidebar [data-view="palestine"]')?.click()};$$('[data-view-help]').forEach(b=>b.onclick=showHelp);
searchInput.oninput=paint;searchInput.onkeydown=e=>{if(e.key==='Enter'&&filtered.length){e.preventDefault();jump(filtered[0]);}};
searchOverlay.addEventListener('click',e=>{if(e.target===searchOverlay)hideSearch()});helpOverlay.addEventListener('click',e=>{if(e.target===helpOverlay)closeHelp()});
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();showSearch();}if(e.key==='Escape'){hideSearch();closeHelp();}});
const setCurrent=()=>{const v=$('.nav.active')?.dataset.view;$('#currentViewTitle').textContent=views[v]||'פלסטין';};
$$('#sidebar .nav').forEach(b=>b.addEventListener('click',setCurrent));window.addEventListener('hashchange',setCurrent);setCurrent();buildIndex();
})();