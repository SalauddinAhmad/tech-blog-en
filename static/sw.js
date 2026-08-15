const CACHE_NAME="tech-intel-v1";
const STATIC_ASSETS=["/css/","/js/","/fonts/","/images/icon-"];
self.addEventListener("install",e=>{self.skipWaiting();});
self.addEventListener("activate",e=>{e.waitUntil(clients.claim());});
self.addEventListener("fetch",e=>{
  const url=new URL(e.request.url);
  const isStatic=STATIC_ASSETS.some(p=>url.pathname.startsWith(p));
  if(isStatic){
    e.respondWith(caches.open(CACHE_NAME).then(c=>c.match(e.request).then(r=>r||fetch(e.request).then(resp=>{if(resp.ok){c.put(e.request,resp.clone());}return resp;}).catch(()=>r))));
  }else{
    e.respondWith(fetch(e.request).then(resp=>{if(resp.ok&&resp.type==="basic"){const clone=resp.clone();caches.open(CACHE_NAME).then(c=>c.put(e.request,clone));}return resp;}).catch(()=>caches.match(e.request)));
  }
});
