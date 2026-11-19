"""Create a redistributable mobile derivative. Run once on the pinned upstream tree."""
from pathlib import Path
import json,re
root=Path(__file__).parent
web=root/'web'
reports=[]
for name in ['atlas_boot.js','atlas_snapshots.js']:
 p=web/'js'/name
 text=p.read_text(encoding='utf-8')
 match=re.search(r'const D = (\{.*?\});',text,re.S)
 if not match: raise ValueError('Unknown packed data format: '+name)
 d=json.loads(match.group(1));before=len(d['f'])
 for key,value in d['d'].items():
  if isinstance(value,dict):
   value['prefectures']=[];value.pop('prefRef',None)
 used=set()
 for value in d['d'].values():
  if isinstance(value,list):used.update(value)
  elif isinstance(value,dict):
   for k in ['polities','regions']:used.update(value.get(k,[]))
 used=sorted(used);remap={old:new for new,old in enumerate(used)}
 d['f']=[d['f'][i] for i in used]
 for k,v in d['d'].items():
  if isinstance(v,list):d['d'][k]=[remap[i] for i in v]
  elif isinstance(v,dict):
   for key in ['polities','regions']:
    if key in v:v[key]=[remap[i] for i in v[key]]
 rings=set()
 for f in d['f']:
  shape=f.get('shape') or {}
  if '_p'in shape:rings.update(shape['_p'])
  if '_m'in shape:
   for poly in shape['_m']:rings.update(poly)
 rings=sorted(rings);ringmap={old:new for new,old in enumerate(rings)}
 d['r']=[d['r'][i] for i in rings]
 for f in d['f']:
  shape=f.get('shape') or {}
  if '_p'in shape:shape['_p']=[ringmap[i] for i in shape['_p']]
  if '_m'in shape:shape['_m']=[[ringmap[i] for i in poly] for poly in shape['_m']]
 text=text[:match.start(1)]+json.dumps(d,ensure_ascii=False,separators=(',',':'))+text[match.end(1):]
 p.write_text('/* Mobile derivative 2026-11-19: CHGIS prefectures and unreferenced geometry removed. GPL-3.0. */\n'+text,encoding='utf-8')
 reports.append(f'{name}: {before} -> {len(d["f"])} features; CHGIS prefectures removed, geometry repacked')
p=web/'js/china_geo_data.js';text=p.read_text(encoding='utf-8')
text,n=re.subn(r'const P = \[.*?\];','const P = []; // Mobile: modern provincial outline layer omitted.',text,count=1,flags=re.S)
assert n==1
p.write_text('/* Mobile derivative 2026-11-19: DataV provincial outlines omitted. */\n'+text,encoding='utf-8')
p=web/'index.html';text=p.read_text(encoding='utf-8')
text=text.replace('width=device-width, initial-scale=1.0','width=device-width, initial-scale=1.0, viewport-fit=cover')
text=re.sub(r'  <script defer src="https://events.vercount.one/js"></script>\s*','',text)
text=re.sub(r'  <script defer src="js/atlas_track.js[^\"]*"></script>\s*','',text)
text=re.sub(r'  <script defer src="https://static.cloudflareinsights.com/[^\n]+\n','',text)
text=re.sub(r'  <link[^>]+href="https://fonts\.[^>]+>\s*','',text)
text=text.replace('</head>','  <link rel="stylesheet" href="mobile.css" />\n</head>')
text=text.replace('</body>','  <script src="mobile.js"></script>\n</body>')
for ident in ['chk-provinces','chk-prov-names']:
 text=re.sub(r'<input type="checkbox" id="'+ident+r'"[^>]*>',f'<input type="checkbox" id="{ident}" disabled title="本版未包含现代省界数据" />',text)
p.write_text('<!-- Independent mobile adaptation, 2026-11-19; GPL-3.0, upstream attribution retained. -->\n'+text,encoding='utf-8')
(web/'MOBILE_NOTICES.txt').write_text('''江山时序 · 手机适配版 0.1
原作者：DeanChensj / Jiangshan Atlas
原项目：https://github.com/DeanChensj/jiangshan-map
修改日期：2026-11-19。独立修改版，非原作者官方发行。
代码与可分发数据采用 GPL-3.0，完整许可见 LICENSE，无任何担保。
本版移除了 CHGIS 来源的郡州府边界及未引用几何，不分发这些受限数据。
本版移除了 DataV 现代省界叠加层，因此省界与省名开关不可用。
政权疆域以 historical-basemaps (GPL-3.0) 为起点；一级政区和历史资料由上游依据史籍整理。
地形基于公有领域 SRTM/GMTED2010/ETOPO1 高程，上游渲染图采用 GPL-3.0。
水系与湖泊：公有领域；古琴录音：上游注明来自 Wikimedia Commons 公有领域。
新增手机底部导航、朝代选择、设备内收藏、安装指引、核心离线缓存；移除第三方统计与外部字体。
完整对应源码随本交付包提供，包含 web、android 及修改与打包脚本。
历史疆域为示意性近似，不作精确或权威边界依据。
''',encoding='utf-8')
(root/'ADAPTATION_REPORT.txt').write_text('\n'.join(reports),encoding='utf-8')
print('\n'.join(reports))
