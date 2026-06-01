// Service worker voor de Uitvaart-Platform app
var CACHE = 'up-app-v8';
var SHELL = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './apple-touch-icon.png'];

self.addEventListener('install', function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){ return c.addAll(SHELL); }).then(function(){ return self.skipWaiting(); }));
});
self.addEventListener('activate', function(e){
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.filter(function(k){ return k !== CACHE; }).map(function(k){ return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});
self.addEventListener('fetch', function(e){
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  // tools en artikelen laden live van hun eigen domein
  if (url.origin !== location.origin) return;
  // articles.json altijd vers ophalen, zodat de carrousel actueel blijft
  if (url.pathname.indexOf('articles.json') !== -1) {
    e.respondWith(
      fetch(req).then(function(res){
        var copy = res.clone();
        caches.open(CACHE).then(function(c){ c.put(req, copy); });
        return res;
      }).catch(function(){ return caches.match(req); })
    );
    return;
  }
  // overige eigen bestanden: eerst uit cache, anders ophalen
  e.respondWith(
    caches.match(req).then(function(cached){
      return cached || fetch(req).then(function(res){
        var copy = res.clone();
        caches.open(CACHE).then(function(c){ c.put(req, copy); });
        return res;
      }).catch(function(){ return caches.match('./index.html'); });
    })
  );
});

// ===== PUSHMELDINGEN =====
// Bij een melding leest de app notify.json van de eigen site uit
// en toont titel + tekst + link die daarin staan.
self.addEventListener('push', function(e){
  e.waitUntil(
    fetch('./notify.json?t=' + Date.now(), { cache: 'no-store' })
      .then(function(r){ return r.json(); })
      .catch(function(){ return {}; })
      .then(function(n){
        var title = (n && n.title) || 'Uitvaart-Platform';
        var body  = (n && n.body)  || 'Er staat nieuwe informatie voor je klaar in de app.';
        var url   = (n && n.url)   || '/';
        return self.registration.showNotification(title, {
          body: body,
          icon: './icon-192.png',
          badge: './icon-192.png',
          data: { url: url }
        });
      })
  );
});

self.addEventListener('notificationclick', function(e){
  e.notification.close();
  var target = (e.notification.data && e.notification.data.url) || '/';
  e.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(list){
      for (var i = 0; i < list.length; i++) {
        if ('focus' in list[i]) return list[i].focus();
      }
      if (self.clients.openWindow) return self.clients.openWindow(target);
    })
  );
});
