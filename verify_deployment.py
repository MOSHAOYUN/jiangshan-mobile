"""Verify a user-supplied HTTPS Pages deployment without account access."""
import argparse,json,urllib.request,urllib.parse,concurrent.futures
p=argparse.ArgumentParser();p.add_argument('url',help='Published HTTPS application URL, including repository subdirectory');args=p.parse_args()
u=urllib.parse.urlsplit(args.url)
if u.scheme!='https' or not u.hostname or u.username or u.password:raise SystemExit('An HTTPS site URL without credentials is required')
base=args.url.rstrip('/')+'/'
checks={'index.html':'mobile.css','manifest.webmanifest':'standalone','mobile.js':'jiangshanMobile','mobile-sw.js':'jiangshan-mobile-v1','js/atlas_snapshots.js':'ATLAS_SNAPSHOTS','assets/icons/icon-192.png':None}
def check(item):
 path,needle=item
 try:
  with urllib.request.urlopen(urllib.request.Request(urllib.parse.urljoin(base,path),headers={'User-Agent':'JiangshanMobileVerification/0.1'}),timeout=30) as r:
   body=r.read();passed=r.status==200 and (needle is None or needle.encode()in body)
   return {'path':path,'status':r.status,'bytes':len(body),'pass':passed}
 except Exception as e:return {'path':path,'pass':False,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(check,checks.items()))
print(json.dumps({'url':base,'checks':results,'pass':all(r['pass']for r in results)},ensure_ascii=False,indent=2))
if not all(r['pass']for r in results):raise SystemExit(1)
