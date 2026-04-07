// Servir recursos desde caché (incluye el ícono personalizado)
self.addEventListener('fetch', function(event) {
  if(event.request.url.endsWith('/custom-icon.png')) {
    event.respondWith(
      caches.open('hotmart-custom-icon').then(cache =>
        cache.match('/custom-icon.png').then(r => r || fetch(event.request))
      )
    );
  }
});

self.addEventListener('push', function(event) {
  const data = event.data ? event.data.json() : {};
  const title = data.title || '🎉 ¡Nueva venta!';
  const options = {
    body: data.body || '',
    icon: data.icon || '',
    badge: data.badge || '',
    vibrate: [200, 100, 200],
    tag: data.tag || 'hotmart-sale',
    renotify: true,
    data: { url: self.location.origin }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data.url || '/'));
});

self.addEventListener('message', function(event) {
  if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
    const { title, body, tag, icon } = event.data;
    self.registration.showNotification(title, {
      body, icon, vibrate: [200, 100, 200],
      tag: tag || 'hotmart-sale', renotify: true,
    });
  }
});
