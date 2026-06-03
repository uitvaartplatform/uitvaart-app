/* Service worker — Uitvaart-Platform
   Ontvangt pushmeldingen voor browser en Android en toont ze.
   Haalt de tekst op bij de verzendserver (Worker), zodat browser/Android
   exact hetzelfde bericht tonen als de iPhone/iPad-app. iOS gebruikt deze
   service worker niet (die werkt via Apple APNs rechtstreeks). */

var NOTIFY_WORKER = "https://uitvaart-push.weathered-dust-cab6.workers.dev/notify.json";

self.addEventListener("install", function(e){ self.skipWaiting(); });
self.addEventListener("activate", function(e){ e.waitUntil(self.clients.claim()); });

self.addEventListener("push", function(event){
  event.waitUntil((async function(){
    var n = { title: "Uitvaart-Platform", body: "" };
    // 1) tekst meegestuurd in de push? gebruik die.
    try{
      if(event.data){ var d = event.data.json(); if(d && (d.title || d.body)) n = d; }
    }catch(e){}
    // 2) anders: haal het laatste bericht op bij de verzendserver; val terug op het lokale bestand.
    if(!n.body && !n.title){ n = { title:"Uitvaart-Platform", body:"" }; }
    try{
      var r = await fetch(NOTIFY_WORKER, { cache:"no-store" });
      if(!r.ok) r = await fetch("./notify.json", { cache:"no-store" });
      if(r.ok){ var j = await r.json(); if(j && (j.title || j.body)) n = j; }
    }catch(e){}

    var opts = {
      body:  n.body || "",
      icon:  n.icon  || "icon-192.png",
      badge: n.badge || "icon-192.png",
      data:  { url: n.url || n.link || "" }
    };
    if(n.image) opts.image = n.image;   // alleen browser/Android tonen een afbeelding
    return self.registration.showNotification(n.title || "Uitvaart-Platform", opts);
  })());
});

self.addEventListener("notificationclick", function(event){
  event.notification.close();
  var url = (event.notification.data && event.notification.data.url) || "";
  event.waitUntil((async function(){
    var all = await self.clients.matchAll({ type:"window", includeUncontrolled:true });
    if(url){
      for(var i=0;i<all.length;i++){ try{ await all[i].focus(); }catch(e){} }
      if(self.clients.openWindow) return self.clients.openWindow(url);
    } else if(all.length){
      try{ return all[0].focus(); }catch(e){}
    }
  })());
});
