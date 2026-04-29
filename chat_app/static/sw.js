// Rooted Feed - Service Worker
// Caches static assets for offline support and faster loading

const CACHE_NAME = 'rooted-v7';  // ← bump this whenever you deploy HTML changes
const STATIC_ASSETS = [
  // NOTE: '/' (HTML) is intentionally NOT cached — always fetch fresh from server
  '/static/manifest.json',
  '/static/favicon.png',
  'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600&family=DM+Sans:wght@300;400;500;700&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.js'
];

// Install event — cache static shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_ASSETS).catch(() => { });
    })
  );
  self.skipWaiting();
});

// Activate event — clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// Fetch event — serve from cache if available, otherwise network
self.addEventListener('fetch', event => {
  // Skip non-GET and socket.io requests (real-time must go to network)
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/socket.io/')) return;
  if (event.request.url.includes('/api/')) return;

  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        // Cache successful responses for static files
        if (response && response.status === 200) {
          const url = new URL(event.request.url);
          if (url.pathname.startsWith('/static/')) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
        }
        return response;
      });
    })
  );
});
