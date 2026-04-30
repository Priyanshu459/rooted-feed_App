// Rooted Feed - Service Worker v2 (Native App Feel)
const CACHE_NAME = 'rooted-pwa-v2';
const OFFLINE_URL = '/offline.html';

const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/icon.png',
  '/static/screenshot.png',
  '/static/favicon.png',
  'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600&family=DM+Sans:wght@300;400;500;700&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.js',
  'https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css'
];

// Install event — cache static shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      // Create a basic offline page if it doesn't exist
      const offlineResponse = new Response(
        '<!DOCTYPE html><html style="background:#FBF7F0;font-family:sans-serif;height:100%;display:flex;align-items:center;justify-content:center;text-align:center;"><body><div style="padding:40px;border-radius:32px;background:#fff;box-shadow:0 20px 40px rgba(0,0,0,0.05);"> <div style="font-size:64px;margin-bottom:20px;">🌲</div> <h1 style="color:#2D1B0E;margin-bottom:10px;">You are offline</h1> <p style="color:#7A6B5A;line-height:1.6;">Rooted Feed needs an internet connection to sync your social tree. We\'ll be back as soon as you\'re reconnected!</p> <button onclick="window.location.reload()" style="margin-top:24px;padding:12px 24px;background:#4A7C59;color:#fff;border:none;border-radius:20px;font-weight:700;cursor:pointer;">Try Again</button> </div></body></html>',
        { headers: { 'Content-Type': 'text/html' } }
      );
      cache.put(OFFLINE_URL, offlineResponse);
      return cache.addAll(STATIC_ASSETS);
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

// Fetch event — Stale-while-revalidate for static assets, Network-first for others
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/socket.io/')) return;
  
  const url = new URL(event.request.url);

  // Static Assets: Cache first then update in background
  if (STATIC_ASSETS.includes(url.pathname) || url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        const fetchPromise = fetch(event.request).then(networkResponse => {
          if (networkResponse && networkResponse.status === 200) {
            const cacheClone = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, cacheClone));
          }
          return networkResponse;
        });
        return cached || fetchPromise;
      })
    );
    return;
  }

  // Navigation: Network first, then offline fallback
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(OFFLINE_URL);
      })
    );
    return;
  }

  // API/Others: Network first
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});
