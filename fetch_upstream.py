import urllib.request,json,pathlib,concurrent.futures,time
root=pathlib.Path(__file__).parent
sha=(root/'UPSTREAM_COMMIT.txt').read_text().strip()
headers={'User-Agent':'Jiangshan-Mobile-Adaptation'}
def get(url):
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=35) as r:return r.read()
  except Exception:
   if attempt==2:raise
items=json.loads(get(f'https://api.github.com/repos/DeanChensj/jiangshan-map/git/trees/{sha}?recursive=1'))['tree']
chosen=[]
for i in items:
 p=i['path']
 if i['type']!='blob':continue
 if p.startswith(('js/','css/','assets/icons/','assets/audio/','assets/terrain/')) or p in ['index.html','LICENSE','README_ZH.md','manifest.webmanifest','sw.js','assets/favicon.svg','assets/terrain_relief.webp','assets/terrain_relief.json']:
  chosen.append(p)
print('Downloading',len(chosen),'runtime/source files',flush=True)
def fetch(p):
 target=root/'web'/p;target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(get(f'https://raw.githubusercontent.com/DeanChensj/jiangshan-map/{sha}/{p}'))
 return p
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
 for n,p in enumerate(pool.map(fetch,chosen),1):
  if n%40==0 or not p.startswith('assets/terrain/'):print(n,p,flush=True)
print('Complete',flush=True)
