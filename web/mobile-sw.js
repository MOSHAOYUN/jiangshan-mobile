/* Mobile derivative 2026-11-19. GPL-3.0. */
const CORE='jiangshan-mobile-v1';
const RUNTIME='jiangshan-mobile-runtime-v1';
const FILES=["./", "./index.html", "./mobile.css", "./mobile.js", "./manifest.webmanifest", "./LICENSE", "./MOBILE_NOTICES.txt", "./assets/terrain_relief.webp", "./js/app.js", "./js/atlas_api.js", "./js/atlas_boot.js", "./js/atlas_narrator.js", "./js/atlas_quiz.js", "./js/atlas_search.js", "./js/atlas_snapshots.js", "./js/atlas_trace.js", "./js/china_geo_data.js", "./js/event_pinyin.js", "./js/i18n_dict.js", "./js/lore_core.js", "./js/lore_detail.js", "./js/map_data.js", "./js/milestone_sources.js", "./js/zh_hant.js", "./css/style.css", "./assets/icons/apple-touch-icon.png", "./assets/icons/icon-192.png", "./assets/icons/icon-512-maskable.png", "./assets/icons/icon-512.png"];
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
