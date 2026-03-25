// Service Worker for PWA and Push Notifications
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installed');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activated');
  event.waitUntil(clients.claim());
});

// Handle push notifications
self.addEventListener('push', (event) => {
  console.log('Push notification received:', event);
  
  let data = {
    title: '💰 Nueva venta',
    body: 'Se ha registrado una nueva venta',
    icon: 'https://i.imgur.com/8YqKQNJ.png'
  };
  
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: data.icon || 'https://i.imgur.com/8YqKQNJ.png',
    badge: 'https://i.imgur.com/8YqKQNJ.png',
    vibrate: [200, 100, 200, 100, 200],
    tag: 'hotmart-sale',
    requireInteraction: false,
    actions: [
      { action: 'view', title: 'Ver detalles' },
      { action: 'close', title: 'Cerrar' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event.action);
  event.notification.close();
  
  if (event.action === 'view' || !event.action) {
    event.waitUntil(
      clients.openWindow('/hotmart-transactions.html')
    );
  }
});

// Cache strategy for offline support
const CACHE_NAME = 'hotmart-v1';
const urlsToCache = [
  '/hotmart-transactions.html',
  '/nueva-venta.html',
  '/manifest.json'
];

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        return response || fetch(event.request);
      })
  );
});
