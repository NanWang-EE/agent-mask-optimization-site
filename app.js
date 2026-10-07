'use strict';
const $=s=>document.querySelector(s);
const video=$('#hero-motion'), toggle=$('#motion-toggle'),slider=$('#round-slider'),roundValue=$('#round-value');
let still=null;
const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function syncMotion(){toggle.textContent=video.paused?'播放动画':'暂停动画';toggle.setAttribute('aria-pressed',String(!video.paused));}
function clearStill(){if(still){still.remove();still=null;}video.hidden=false;video.style.display='block';}
function playMotion(){clearStill();video.play().catch(()=>syncMotion());}
toggle.addEventListener('click',()=>{if(still||video.paused)playMotion();else video.pause();});
$('#resume-motion').addEventListener('click',playMotion);
video.addEventListener('play',syncMotion);video.addEventListener('pause',syncMotion);
if(reduced){video.autoplay=false;video.pause();video.currentTime=0;}syncMotion();
slider.addEventListener('input',()=>{video.pause();if(!still){still=document.createElement('img');still.width=1440;still.height=720;video.after(still);}const r=Number(slider.value);still.src=`assets/frames/round-${String(r).padStart(2,'0')}.png`;still.alt=`Astra 第 ${r} 轮结束后的两个保留 mask`;video.hidden=true;video.style.display='none';roundValue.textContent=`${String(r).padStart(2,'0')} / 15`;});
video.addEventListener('timeupdate',()=>{if(still)return;let time=video.currentTime,round=0;for(let i=0;i<16;i++){const span=(i===0||i===15?1.7:1)+.49;if(time<span){round=i;break;}time-=span;round=i;}slider.value=String(round);roundValue.textContent=`${String(round).padStart(2,'0')} / 15`;});
document.querySelectorAll('[data-input]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-input]').forEach(x=>{x.classList.toggle('selected',x===b);x.setAttribute('aria-pressed',String(x===b));});const path=`assets/${b.dataset.input}.png`;$('#input-image').src=path;$('#input-image-link').href=path;$('#input-image').alt=b.dataset.input==='overview'?'Case 1 第一轮实际输入概览图':'Case 1 第一轮实际输入热点与边段 ID 标注图';}));
const data=window.MASK_DATA;
if(!data){$('#charts').innerHTML='<p class="data-error">数据未能载入，请刷新页面。可通过下方链接下载完整图表。</p>';}else{
const n=v=>v===null?'—':Number(v).toLocaleString('en-US');
$('#prompt-excerpt').textContent=data.prompt.split('\n\n').slice(0,2).join('\n\n');
$('#proposal-excerpt').textContent=JSON.stringify({case_id:'M1_test1',iteration:0,moves:data.example.sampleMoves.slice(3,6)},null,2)+'\n\n// 展示 3 / 99 条真实动作；iteration 为零起始编号。';
let activeCase=1;
function chart(metric,title,subtitle){
 const series=data.series.filter(s=>s.case===activeCase&&($('#sraf-series').checked||s.variant!=='astra_sraf'));
 const max={epe:100,pvband:80000,l2:125000}[metric];const W=400,H=300,left=57,right=20,top=24,bottom=53;
 const x=r=>left+r/15*(W-left-right),y=v=>H-bottom-v/max*(H-top-bottom);
 let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="title-${metric} desc-${metric}"><title id="title-${metric}">Case ${activeCase} ${title} 随优化轮次变化</title><desc id="desc-${metric}">显示各模型从初始状态至第十五轮的保留指标，完整数值在下方展开表格中。</desc>`;
 for(let i=0;i<=4;i++){const v=i*max/4;svg+=`<line x1="${left}" y1="${y(v)}" x2="${W-right}" y2="${y(v)}" stroke="#303030"/><text x="${left-10}" y="${y(v)+4}" text-anchor="end" fill="#999" font-size="12">${metric==='epe'?v:`${v/1000}k`}</text>`;}
 for(const r of [0,3,6,9,12,15])svg+=`<text x="${x(r)}" y="${H-bottom+25}" text-anchor="middle" fill="#aaa" font-size="12">${r}</text>`;
 svg+=`<text x="${(W+left-right)/2}" y="${H-6}" text-anchor="middle" fill="#999" font-size="12">提案轮次 · 0 为初始状态</text>`;
 if(metric==='pvband'){const ceiling=activeCase===1?73398.4:59256;svg+=`<line x1="${left}" x2="${W-right}" y1="${y(ceiling)}" y2="${y(ceiling)}" stroke="#999" stroke-dasharray="3 5"/><text x="${W-right}" y="${y(ceiling)-7}" text-anchor="end" fill="#aaa" font-size="11">固定上限 ${n(ceiling)}</text>`;}
 for(const s of series){svg+=`<polyline fill="none" stroke="${s.color}" stroke-width="2.4" ${s.variant==='astra_sraf'?'stroke-dasharray="6 4"':''} points="${s.points.map(p=>`${x(p.round)},${y(p[metric])}`).join(' ')}"/>`;for(const p of s.points)svg+=`<circle cx="${x(p.round)}" cy="${y(p[metric])}" r="2.7" fill="${s.color}"><title>${s.label} · 第 ${p.round} 轮 · ${title}: ${n(p[metric])}</title></circle>`;}
 return `<article class="chart"><h3>${title} <span aria-hidden="true">↓</span></h3><p>${subtitle}</p>${svg}</svg></article>`;
}
function renderCharts(){
 $('#charts').innerHTML=chart('epe','EPE','名义违例数 · 15 nm 阈值')+chart('pvband','PVB','工艺变化带面积 / nm²')+chart('l2','L2','名义二值平方误差 / nm²');
 const selected=data.series.filter(s=>s.case===activeCase&&($('#sraf-series').checked||s.variant!=='astra_sraf'));
 $('#round-values').innerHTML='<caption>当前 case 各轮保留指标；每格依次为 EPE / PVB / L2。</caption><thead><tr><th scope="col">轮次</th>'+selected.map(s=>`<th scope="col">${s.label}</th>`).join('')+'</tr></thead><tbody>'+Array.from({length:16},(_,i)=>`<tr><th scope="row">${i}</th>${selected.map(s=>`<td>${n(s.points[i].epe)} / ${n(s.points[i].pvband)} / ${n(s.points[i].l2)}</td>`).join('')}</tr>`).join('')+'</tbody>';
 const existing=$('#sraf-legend');if(existing)existing.remove();if($('#sraf-series').checked){const s=document.createElement('span');s.id='sraf-legend';s.innerHTML='<i style="--dot:#be9ce8"></i>Astra + SRAF 推荐';$('.legend').append(s);}
}
document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>{activeCase=Number(b.dataset.case);document.querySelectorAll('[data-case]').forEach(x=>{x.classList.toggle('selected',x===b);x.setAttribute('aria-pressed',String(x===b));});renderCharts();}));
$('#sraf-series').addEventListener('change',renderCharts);renderCharts();
const cells=cases=>cases.map(c=>`<td>${n(c.epe)}</td><td>${n(c.pvband)}</td><td>${n(c.l2)}</td>`).join('');
let rows=data.baselines.rows.map(b=>`<tr><td>${b.method}</td><td class="source-cell">${b.source==='Original'?'原方法报告值':'OpenILT 复现'} · 表 ${b.table}</td>${cells(b.cases)}</tr>`).join('');
for(const [i,variant] of ['astra','sol6','sol56','astra_sraf'].entries()){const ss=data.series.filter(s=>s.variant===variant).sort((a,b)=>a.case-b.case);rows+=`<tr class="our-row ${i===0?'group-start':''}"><td>${ss[0].label.replace(' + SRAF guidance',' + SRAF 推荐')}</td><td class="source-cell">本项目 · 15 轮${variant==='astra'?' · 历史参考':''}</td>${cells(ss.map(s=>s.points.at(-1)))}</tr>`;}
$('#benchmark-body').innerHTML=rows;
}
