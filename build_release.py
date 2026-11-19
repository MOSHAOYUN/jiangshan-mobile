"""Package the modified source and runnable static site; no public deployment."""
from pathlib import Path
import json,zipfile,shutil
root=Path(__file__).parent;web=root/'web'
core=['./','./index.html','./mobile.css','./mobile.js','./manifest.webmanifest','./LICENSE','./MOBILE_NOTICES.txt','./assets/terrain_relief.webp']
core += ['./'+p.relative_to(web).as_posix() for p in sorted((web/'js').glob('*.js')) if p.name!='atlas_track.js']
core += ['./css/style.css']
core += ['./'+p.relative_to(web).as_posix() for p in sorted((web/'assets/icons').glob('*.png'))]
sw='''/* Mobile derivative 2026-11-19. GPL-3.0. */
const CORE='jiangshan-mobile-v1';
const RUNTIME='jiangshan-mobile-runtime-v1';
const FILES=__FILES__;
self.addEventListener('install',event=>event.waitUntil(caches.open(CORE).then(cache=>cache.addAll(FILES)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('jiangshan-mobile-')&&k!==CORE&&k!==RUNTIME).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
 const req=event.request,url=new URL(req.url);
 if(req.method!=='GET'||url.origin!==self.location.origin||!url.pathname.startsWith(new URL(self.registration.scope).pathname))return;
 event.respondWith((async()=>{
  const core=await caches.open(CORE);
  if(req.mode==='navigate'){
   try{const response=await fetch(req);if(response.ok)return response;}catch{}
   return (await core.match('./index.html')) || Response.error();
  }
  const match=await core.match(req,{ignoreSearch:true});if(match)return match;
  const runtime=await caches.open(RUNTIME),saved=await runtime.match(req);if(saved)return saved;
  try{const response=await fetch(req);if(response.ok&&url.pathname.includes('/assets/terrain/')){await runtime.put(req,response.clone());const keys=await runtime.keys();if(keys.length>100)await runtime.delete(keys[0]);}return response;}catch{return Response.error();}
 })());
});
'''.replace('__FILES__',json.dumps(core,ensure_ascii=False))
(web/'mobile-sw.js').write_text(sw,encoding='utf-8')
# Android project reads the same directory; copy only application resources, without dev tooling.
assets=root/'android/app/src/main/assets/web'
shutil.copytree(web,assets,dirs_exist_ok=True)
icon=root/'android/app/src/main/res/drawable/app_icon.png'
icon.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(web/'assets/icons/icon-192.png',icon)
release=root/'release';release.mkdir(exist_ok=True)
paths=[]
for p in root.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(root)
 allowed_roots={'web','android'}
 allowed_files={'adapt.py','build_release.py','fetch_upstream.py','prepare_pages.py','audit_pages.py','verify-mobile.cjs','verify_deployment.py','UPSTREAM_COMMIT.txt','ADAPTATION_REPORT.txt','使用说明.md','验证结果.md','package.json','pnpm-lock.yaml'}
 if rel.parts[0] not in allowed_roots and rel.as_posix() not in allowed_files:continue
 if any(x in rel.parts for x in ['node_modules','release','test-artifacts','__pycache__','.gradle']):continue
 if p.name=='local.properties' or p.suffix in {'.jks','.keystore'}:continue
 if rel.parts[:3]==('android','app','build'):continue
 # The Android build task performs this copy. Avoid duplicating assets in source package.
 if rel.parts[:6]==('android','app','src','main','assets','web'):continue
 paths.append((p,rel))
with zipfile.ZipFile(release/'江山时序_手机适配版_源码与部署包.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p,rel in paths:z.write(p,'jiangshan-mobile/'+rel.as_posix())
with zipfile.ZipFile(release/'江山时序_手机网站部署包.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in web.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(web).as_posix())
print('Core cache files:',len(core))
print('Release:',release/'江山时序_手机适配版_源码与部署包.zip')
