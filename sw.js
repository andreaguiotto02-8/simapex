// Service worker di Simapex: tiene l'app in memoria per usarla senza rete.
// Aumenta il numero di versione quando carichi una nuova versione dell'app.
const CACHE = 'simapex-0.82';
const FILES = ['./', 'index.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'icon-maskable-192.png', 'icon-maskable-512.png', 'catalogo-acc.json', 'orbitron-900.woff2'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(FILES.map(f => fetch(new Request(f, {cache: 'reload'})).then(r => { if (r.ok) return c.put(f, r); })))).catch(() => {}).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});
// Prima la rete (sempre la versione più nuova), poi la copia salvata se la rete manca o è troppo lenta.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;
  e.respondWith((async () => {
    const cached = () => caches.match(e.request, { ignoreSearch: true });
    const net = fetch(e.request, { cache: 'no-cache' }).then(r => {
      if (r && r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)).catch(() => {}); }
      return r;
    });
    const old = await cached();
    if (!old) return net;
    // con una copia già salvata: se la rete non risponde entro 8 secondi si parte comunque dalla copia
    const slow = new Promise(res => setTimeout(() => res(old), 8000));
    return Promise.race([net.catch(() => old), slow]);
  })());
});
