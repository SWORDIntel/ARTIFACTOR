/* eslint-disable no-restricted-globals */

// ARTIFACTOR PWA Service Worker
// Provides offline support and caching for the enterprise artifact management platform

const CACHE_NAME = 'artifactor-v3.0.0';
const API_CACHE_NAME = 'artifactor-api-v3.0.0';

// URLs to cache for offline functionality
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/dashboard',
  '/artifacts',
  '/search',
  '/manifest.json',
];

// API endpoints to cache
const apiEndpoints = [
  '/api/v1/auth/me',
  '/api/v1/artifacts',
  '/api/v1/notifications',
];

// Install event - cache essential resources
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('[SW] Skip waiting');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[SW] Claiming clients');
      return self.clients.claim();
    })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle API requests with network-first strategy
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      caches.open(API_CACHE_NAME).then((cache) => {
        return fetch(request).then((response) => {
          // Cache successful responses
          if (response.status === 200) {
            cache.put(request, response.clone());
          }
          return response;
        }).catch(() => {
          // Return cached version if network fails
          console.log('[SW] Network failed, serving from cache:', request.url);
          return cache.match(request);
        });
      })
    );
    return;
  }

  // Handle app shell with cache-first strategy
  if (request.mode === 'navigate') {
    event.respondWith(
      caches.match('/').then((response) => {
        return response || fetch(request);
      })
    );
    return;
  }

  // Handle static resources with cache-first strategy
  event.respondWith(
    caches.match(request).then((response) => {
      if (response) {
        return response;
      }

      return fetch(request).then((response) => {
        // Don't cache non-successful responses
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }

        // Clone the response for caching
        const responseToCache = response.clone();

        caches.open(CACHE_NAME).then((cache) => {
          cache.put(request, responseToCache);
        });

        return response;
      });
    })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);

  if (event.tag === 'artifact-sync') {
    event.waitUntil(syncArtifacts());
  }
});

// Push notifications
self.addEventListener('push', (event) => {
  console.log('[SW] Push received:', event);

  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: '/logo192.png',
      badge: '/logo192.png',
      image: data.image,
      data: data.data,
      actions: data.actions || [],
      tag: data.tag || 'artifactor-notification',
      requireInteraction: data.requireInteraction || false,
      silent: data.silent || false,
      vibrate: [200, 100, 200],
    };

    event.waitUntil(
      self.registration.showNotification(data.title || 'ARTIFACTOR', options)
    );
  }
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event);

  event.notification.close();

  if (event.action) {
    // Handle action buttons
    if (event.action === 'view') {
      event.waitUntil(
        clients.openWindow(event.notification.data?.url || '/')
      );
    }
  } else {
    // Handle notification body click
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        // Focus existing window if available
        for (const client of clientList) {
          if (client.url === '/' && 'focus' in client) {
            return client.focus();
          }
        }
        // Open new window if no existing window
        if (clients.openWindow) {
          return clients.openWindow('/');
        }
      })
    );
  }
});

// Helper function to sync artifacts when back online
async function syncArtifacts() {
  try {
    console.log('[SW] Syncing artifacts...');

    // Get pending artifact updates from IndexedDB
    const pendingUpdates = await getPendingUpdates();

    for (const update of pendingUpdates) {
      try {
        const response = await fetch('/api/v1/artifacts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(update),
        });

        if (response.ok) {
          await removePendingUpdate(update.id);
          console.log('[SW] Synced artifact:', update.id);
        }
      } catch (error) {
        console.error('[SW] Failed to sync artifact:', update.id, error);
      }
    }
  } catch (error) {
    console.error('[SW] Background sync failed:', error);
  }
}

// Helper function to get pending updates (placeholder)
async function getPendingUpdates() {
  // This would integrate with IndexedDB to get pending offline changes
  return [];
}

// Helper function to remove pending update (placeholder)
async function removePendingUpdate(id) {
  // This would remove the synced update from IndexedDB
  console.log('[SW] Removed pending update:', id);
}