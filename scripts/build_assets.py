"""Render cached experiment artifacts only; no model calls or optical simulation."""
from pathlib import Path
import csv, json, shutil, hashlib, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
os.environ.setdefault('MPLCONFIGDIR','/tmp/mask-site-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter
SITE=Path(__file__).resolve().parents[1]
ROOT=SITE.parent
A=SITE/'assets'; D=SITE/'data'; PRIVATE=SITE/'private-evidence'
PRIVATE.mkdir(exist_ok=True)
for p in [A/'frames',A/'figures',D]:p.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text())
manifest=[]
def record(p):
 manifest.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
summaries=list(csv.DictReader((ROOT/'results/model15_study/summary.csv').open()))
rounds=list(csv.DictReader((ROOT/'results/model15_study/rounds.csv').open()))
record(ROOT/'results/model15_study/summary.csv');record(ROOT/'results/model15_study/rounds.csv')
labels={'astra':'Astra 6','sol6':'Sol 6','sol56':'Sol 5.6','astra_sraf':'Astra 6 + SRAF guidance'}
colors={'astra':'#c6f58b','sol6':'#8fbafa','sol56':'#eab48b','astra_sraf':'#be9ce8'}
series=[]
for s in summaries:
 rs=sorted([r for r in rounds if r['case_id']==s['case_id'] and r['variant']==s['variant']],key=lambda r:int(r['iteration']))
 assert [int(r['iteration']) for r in rs]==list(range(15))
 points=[{'round':0,'epe':int(s['seed_epe']),'l2':int(s['seed_l2']),'pvband':int(s['seed_pvband']),'accepted':None}]
 for r in rs:
  points.append({'round':int(r['iteration'])+1,'epe':int(r['retained_epe']),'l2':int(r['retained_l2']),'pvband':int(r['retained_pvband']),'accepted':r['accepted']=='True','reason':r['acceptance_reason'] or r['error']})
 assert all(points[-1][m]==int(s['final_'+m]) for m in ['epe','l2','pvband'])
 series.append({'case':int(s['case_id'][-1]),'variant':s['variant'],'label':labels[s['variant']],'model':s['model'],'color':colors[s['variant']],'points':points,'historical':s['historical_reference']=='True','finalSrafs':int(s['final_sraf_count'])})
(D/'trajectories.json').write_text(json.dumps(series,indent=2)+'\n')
with (D/'trajectories.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['case','variant','model','round','epe','l2','pvband','accepted','reason']);w.writeheader()
 for s in series:
  for p in s['points']:w.writerow({'case':s['case'],'variant':s['variant'],'model':s['model'],**p})
# Original and reproduced method values transcribed from OpenILT ASICON 2023 Tables I/II, page 3.
base=[('MOSAIC','Original',[(6,65534,49893),(10,48230,50369)]),('MOSAIC','OpenILT',[(8,55028,48896),(4,46019,37327)]),('LevelSet','Original',[(4,62693,46032),(1,50724,36177)]),('LevelSet','OpenILT',[(6,57468,45520),(1,49680,33571)]),('GAN-OPC','Original',[(None,58043,55425),(None,53020,40211)]),('GAN-OPC','OpenILT',[(20,52126,58712),(1,43861,36669)]),('MultiLevel','Original',[(3,46077,39303),(0,37626,28986)]),('MultiLevel','OpenILT',[(4,47367,38577),(1,37572,32104)])]
baselines=[]
for method,source,cases in base:
 baselines.append({'method':method,'source':source,'table':'I' if method in ['MOSAIC','LevelSet'] else 'II','cases':[{'case':i+1,'epe':v[0],'pvband':v[1],'l2':v[2]} for i,v in enumerate(cases)]})
(D/'baselines.json').write_text(json.dumps({'paper':'https://www.cse.cuhk.edu.hk/~byu/papers/C179-ASICON2023-OpenILT.pdf','page':3,'rows':baselines},indent=2)+'\n')
with (D/'baselines.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['method','source','paper_table','case','epe','pvband_nm2','l2_nm2'])
 for b in baselines:
  for c in b['cases']:w.writerow([b['method'],b['source'],b['table'],c['case'],c['epe'],c['pvband'],c['l2']])
# Replay acceptance decisions. Rejected rounds keep the previous retained array.
all_masks=[]; frame_info=[]
for c in [1,2]:
 run=ROOT/f'runs/coldstart15_case{c}'
 mask=np.load(run/'start/mask.npy',allow_pickle=False); masks=[mask]
 record(run/'start/mask.npy')
 info=[{'round':0,'source':str((run/'start/mask.npy').relative_to(ROOT)),'accepted':None}]
 for i in range(15):
  p=run/f'round_{i:03d}'; t=read(p/'trial.json'); record(p/'trial.json')
  assert not any(t.get(k) for k in ['sraf_add','sraf_update','sraf_delete'])
  if t['accepted']:
   mask=np.load(p/'candidate/mask.npy',allow_pickle=False);record(p/'candidate/mask.npy')
  masks.append(mask)
  info.append({'round':i+1,'accepted':t['accepted'],'source':str((p/'candidate/mask.npy').relative_to(ROOT)) if t['accepted'] else info[-1]['source']})
 assert np.array_equal(masks[-1],np.load(run/'best/mask.npy',allow_pickle=False))
 all_masks.append(masks); frame_info.append(info)
occupied=np.logical_or.reduce([m.astype(bool) for masks in all_masks for m in masks])
y,x=np.nonzero(occupied);span=int(max(x.max()-x.min(),y.max()-y.min())+130);cx=(x.min()+x.max())//2;cy=(y.min()+y.max())//2
box=(int(cx-span//2),int(cy-span//2),int(cx-span//2+span),int(cy-span//2+span));x0,y0,x1,y1=box
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
if not Path(fontpath).exists():fontpath='/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf'
font=lambda n:ImageFont.truetype(fontpath,n)
frames=[]
for i in range(16):
 im=Image.new('L',(1440,720),8); draw=ImageDraw.Draw(im)
 draw.line((720,45,720,660),fill=40,width=1)
 for j in [0,1]:
  mask=all_masks[j][i];thumb=Image.fromarray(np.where(mask[y0:y1,x0:x1][::-1],240,8).astype('uint8')).resize((565,565),Image.Resampling.LANCZOS)
  off=j*720;im.paste(thumb,(off+78,67))
  draw.text((off+34,24),f'CASE 0{j+1}',font=font(18),fill=190)
  draw.text((off+532,24),f'ROUND {i:02d} / 15',font=font(16),fill=150)
  p=next(s for s in series if s['variant']=='astra' and s['case']==j+1)['points'][i]
  draw.text((off+34,652),f'EPE {p["epe"]:02d}     L2 {p["l2"]:,}     PVB {p["pvband"]:,}',font=font(17),fill=190)
  state='INITIAL' if i==0 else ('ACCEPTED' if p['accepted'] else 'RETAINED / ROLLBACK')
  draw.text((off+34,684),state,font=font(12),fill=110)
 im.save(A/f'frames/round-{i:02d}.png');frames.append(im)
frames[-1].save(A/'poster.png')
# Smoothstep crossfades are presentation only, never scored physical masks.
animation=[];durations=[]
for i,im in enumerate(frames):
 animation.append(im);durations.append(1000 if i not in [0,15] else 1700)
 nxt=frames[(i+1)%len(frames)]
 for t in np.linspace(0,1,9)[1:-1]:
  animation.append(Image.blend(im,nxt,float(t*t*(3-2*t))));durations.append(70)
animation[0].save(A/'optimization.gif',save_all=True,append_images=animation[1:],duration=durations,loop=0,optimize=True,disposal=1)
(D/'animation.json').write_text(json.dumps({'source':'coldstart15_case{1,2}; SRAF guidance off','coordinate_crop_xyxy':box,'orientation':'x right, y up; array rows flipped for display','frames':frame_info,'transition':'smoothstep opacity crossfade, not an evaluated intermediate mask','duration_ms':sum(durations)},indent=2)+'\n')
# The exact first-round images, prompt, state, and structured final proposal.
r=ROOT/'runs/coldstart15_case1/round_000'
for filename in ['overview.png','hotspots.png']:
 shutil.copyfile(r/'input'/filename,A/filename);record(r/'input'/filename)
for src,dest in [(r/'codex/prompt.txt','prompt.txt'),(r/'state.json','state.json'),(r/'proposal.json','proposal.json')]:
 text=src.read_text().replace(str(ROOT),'[workspace]');(PRIVATE/dest).write_text(text);record(src)
(D/'prompt-instructions.txt').write_text((PRIVATE/'prompt.txt').read_text().split('BEGIN SUPPLIED STATE JSON')[0].strip()+'\n')
trial=read(r/'trial.json');state=read(r/'state.json');proposal=read(r/'proposal.json')
(D/'example.json').write_text(json.dumps({'case':1,'round':1,'before':trial['before_metrics'],'after':trial['candidate_metrics'],'accepted':trial['accepted'],'reason':trial['acceptance_reason'],'summary':trial['proposal_summary'],'moves':len(proposal['moves']),'segments':len(state['segments']),'pvband_limit':state['optimization']['pvband_limit'],'sampleMoves':proposal['moves'][:7]},indent=2)+'\n')
# Scientific figures: comparable axes per metric, explicit round zero and PVB limits.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
for theme in ['dark','light']:
 bg='#121212' if theme=='dark' else 'white';fg='#c9c9c9' if theme=='dark' else '#333333';grid='#333333' if theme=='dark' else '#dddddd'
 palette=colors if theme=='dark' else dict(zip(labels,['#517e23','#2869b0','#b9692a','#8e53ab']))
 fig,axs=plt.subplots(2,3,figsize=(15,8),facecolor=bg,layout='constrained')
 for ci in [1,2]:
  for mi,(metric,name) in enumerate([('epe','EPE violations'),('pvband','PVB (nm²)'),('l2','Squared L2 (nm²)')]):
   ax=axs[ci-1,mi];ax.set_facecolor(bg)
   for s in series:
    if s['case']!=ci:continue
    ax.plot([p['round'] for p in s['points']],[p[metric] for p in s['points']],label=s['label'],color=palette[s['variant']],lw=2,linestyle='--' if s['variant']=='astra_sraf' else '-',marker='o',markersize=3)
   if metric=='pvband':ax.axhline([73398.4,59256][ci-1],ls=':',color=fg,lw=1,label='PVB ceiling')
   ax.set_title(f'Case {ci} · {name}',color=fg,loc='left',pad=14);ax.set_xlabel('Proposal round (0 = initial target)',color=fg)
   ax.set_xlim(0,15);ax.set_xticks([0,3,6,9,12,15]);ax.set_ylim(bottom=0,top={'epe':95,'pvband':78000,'l2':125000}[metric]);ax.tick_params(colors=fg);ax.grid(axis='y',color=grid,alpha=.6)
   if metric=='epe':ax.yaxis.set_major_locator(MaxNLocator(integer=True,nbins=5))
   else:ax.yaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x/1000:g}k'))
   for spine in ax.spines.values():spine.set_color(grid)
   if ci==1:ax.legend(fontsize=8,frameon=False,labelcolor=fg,loc='upper right' if metric!='pvband' else 'lower right')
 fig.suptitle('Native agent mask optimization · retained masks across 15 proposals',color=fg,fontsize=16)
 for ext in ['png','svg','pdf']:fig.savefig(A/'figures'/f'convergence-{theme}.{ext}',dpi=180,facecolor=bg)
 plt.close(fig)
# Concrete before/after mask and print contours from the saved simulation.
fig,axes=plt.subplots(1,2,figsize=(12,6),layout='constrained')
for ax,label,path in [(axes[0],'Input · target mask',ROOT/'runs/coldstart15_case1/start'),(axes[1],'Output · accepted proposal',r/'candidate')]:
 mask=np.load(path/'mask.npy',allow_pickle=False)
 sim=np.load(path/'simulation.npz',allow_pickle=False)['printed_nom']
 ax.imshow(mask[y0:y1,x0:x1],origin='lower',cmap='Greys',extent=(x0,x1,y0,y1),interpolation='nearest',vmin=0,vmax=1,alpha=.8)
 ax.contour(np.arange(x0,x1),np.arange(y0,y1),sim[y0:y1,x0:x1],levels=[.5],colors=['#598e23'],linewidths=1)
 ax.set_title(label);ax.set_xlabel('x (nm)');ax.set_ylabel('y (nm)')
fig.suptitle('Case 1 · round 1 | black: mask · green: nominal printed contour')
fig.savefig(A/'example-before-after.png',dpi=150);plt.close(fig)
(D/'provenance.json').write_text(json.dumps({'sources':manifest,'paper':{'url':'https://www.cse.cuhk.edu.hk/~byu/papers/C179-ASICON2023-OpenILT.pdf','page':3,'tables':['I','II'],'scope':'Only case1 and case2; no 10-case averages used.'},'notes':['No new simulation or model calls.','Round numbers on the site are 1-based; stored iteration numbers are 0-based.','Public example omits raw internal event streams; only final structured proposal is exported.','Absolute workspace paths, if present in the example input, are replaced with [workspace].']},indent=2)+'\n')
print(json.dumps({'series':len(series),'points':sum(len(s['points']) for s in series),'frames':len(frames),'gif_bytes':(A/'optimization.gif').stat().st_size,'crop':box}))
