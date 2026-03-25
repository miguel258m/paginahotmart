// Service Worker for Push Notifications
self.addEventListener('install', (event) => {
  console.log('Service Worker installed');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('Service Worker activated');
  event.waitUntil(clients.claim());
});

self.addEventListener('push', (event) => {
  console.log('Push received:', event);
  
  const data = event.data ? event.data.json() : {
    title: '💰 Nueva venta',
    body: 'Se ha registrado una nueva venta',
    icon: 'https://i.imgur.com/8YqKQNJ.png'
  };

  const options = {
    body: data.body,
    icon: data.icon || 'https://i.imgur.com/8YqKQNJ.png',
    badge: data.icon || 'https://i.imgur.com/8YqKQNJ.png',
    vibrate: [200, 100, 200],
    tag: 'new-sale',
    requireInteraction: false
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked');
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('/')
  );
});
