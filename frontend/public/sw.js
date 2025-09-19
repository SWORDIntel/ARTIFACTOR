// ARTIFACTOR v3.0 Service Worker
// Mobile-optimized PWA with offline capabilities and background sync

const CACHE_NAME = 'artifactor-v3-cache-v1';
const STATIC_CACHE_NAME = 'artifactor-static-v1';
const DYNAMIC_CACHE_NAME = 'artifactor-dynamic-v1';
const API_CACHE_NAME = 'artifactor-api-v1';

// Resources to cache immediately
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/favicon.ico',
  'https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap',
  'https://fonts.googleapis.com/icon?family=Material+Icons'
];

// API endpoints to cache with special strategies
const API_CACHE_PATTERNS = [
  /\/api\/artifacts/,
  /\/api\/auth\/profile/,
  /\/api\/dashboard/,
  /\/api\/agents\/status/
];

// Maximum cache sizes
const MAX_CACHE_SIZE = {
  static: 50,
  dynamic: 100,
  api: 200
};

// Cache duration (in milliseconds)
const CACHE_DURATION = {
  static: 7 * 24 * 60 * 60 * 1000, // 7 days
  api: 5 * 60 * 1000, // 5 minutes
  artifacts: 30 * 60 * 1000 // 30 minutes
};

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Static assets cached successfully');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('[SW] Failed to cache static assets:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE_NAME &&
                cacheName !== DYNAMIC_CACHE_NAME &&
                cacheName !== API_CACHE_NAME) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[SW] Service worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Handle different request types with appropriate strategies
  if (request.url.includes('/api/')) {
    event.respondWith(handleApiRequest(request));
  } else if (request.destination === 'image') {
    event.respondWith(handleImageRequest(request));
  } else if (STATIC_ASSETS.some(asset => request.url.includes(asset))) {
    event.respondWith(handleStaticAssets(request));
  } else {
    event.respondWith(handleDynamicContent(request));
  }
});

// API request handler - Network first with fallback to cache
async function handleApiRequest(request) {
  const url = new URL(request.url);

  try {
    // Try network first
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Cache successful API responses
      const cache = await caches.open(API_CACHE_NAME);
      const responseClone = networkResponse.clone();

      // Add timestamp for cache expiration
      const response = new Response(responseClone.body, {
        status: responseClone.status,
        statusText: responseClone.statusText,
        headers: {
          ...Object.fromEntries(responseClone.headers.entries()),
          'sw-cached-at': Date.now().toString()
        }
      });

      await cache.put(request, response);
      await limitCacheSize(API_CACHE_NAME, MAX_CACHE_SIZE.api);

      return networkResponse;
    }
  } catch (error) {
    console.log('[SW] Network failed, trying cache for:', request.url);
  }

  // Fallback to cache
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    // Check if cached response is still valid
    const cachedAt = cachedResponse.headers.get('sw-cached-at');
    if (cachedAt && (Date.now() - parseInt(cachedAt)) < CACHE_DURATION.api) {
      return cachedResponse;
    }
  }

  // Return offline fallback for critical endpoints
  if (url.pathname.includes('/artifacts')) {
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'This content is not available offline',
        cached: false
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }

  throw new Error('Network and cache failed');
}

// Static assets handler - Cache first
async function handleStaticAssets(request) {
  const cachedResponse = await caches.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  // Fetch and cache if not found
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      await cache.put(request, networkResponse.clone());
      await limitCacheSize(STATIC_CACHE_NAME, MAX_CACHE_SIZE.static);
    }

    return networkResponse;
  } catch (error) {
    console.error('[SW] Failed to fetch static asset:', request.url, error);
    throw error;
  }
}

// Image request handler - Cache first with stale-while-revalidate
async function handleImageRequest(request) {
  const cache = await caches.open(DYNAMIC_CACHE_NAME);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    // Return cached version immediately
    const fetchPromise = fetch(request)
      .then(response => {
        if (response.ok) {
          cache.put(request, response.clone());
        }
        return response;
      })
      .catch(() => cachedResponse);

    return cachedResponse;
  }

  // No cache, fetch from network
  try {
    const response = await fetch(request);

    if (response.ok) {
      await cache.put(request, response.clone());
      await limitCacheSize(DYNAMIC_CACHE_NAME, MAX_CACHE_SIZE.dynamic);
    }

    return response;
  } catch (error) {
    console.error('[SW] Failed to fetch image:', request.url, error);
    throw error;
  }
}

// Dynamic content handler - Network first with cache fallback
async function handleDynamicContent(request) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      await cache.put(request, networkResponse.clone());
      await limitCacheSize(DYNAMIC_CACHE_NAME, MAX_CACHE_SIZE.dynamic);
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache for:', request.url);

    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const offlinePage = await caches.match('/');
      if (offlinePage) {
        return offlinePage;
      }
    }

    throw error;
  }
}

// Utility function to limit cache size
async function limitCacheSize(cacheName, maxSize) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();

  if (keys.length > maxSize) {
    const keysToDelete = keys.slice(0, keys.length - maxSize);
    await Promise.all(keysToDelete.map(key => cache.delete(key)));
  }
}

// Background sync for offline actions
self.addEventListener('sync', event => {
  console.log('[SW] Background sync event:', event.tag);

  if (event.tag === 'upload-artifact') {
    event.waitUntil(processOfflineUploads());
  } else if (event.tag === 'sync-collaboration') {
    event.waitUntil(syncCollaborationData());
  }
});

// Process offline artifact uploads when connection is restored
async function processOfflineUploads() {
  try {
    const db = await openIndexedDB();
    const uploads = await getOfflineUploads(db);

    for (const upload of uploads) {
      try {
        const response = await fetch('/api/artifacts/upload', {
          method: 'POST',
          body: upload.data
        });

        if (response.ok) {
          await removeOfflineUpload(db, upload.id);

          // Notify all clients about successful upload
          const clients = await self.clients.matchAll();
          clients.forEach(client => {
            client.postMessage({
              type: 'UPLOAD_SYNCED',
              payload: { uploadId: upload.id }
            });
          });
        }
      } catch (error) {
        console.error('[SW] Failed to sync upload:', upload.id, error);
      }
    }
  } catch (error) {
    console.error('[SW] Failed to process offline uploads:', error);
  }
}

// Sync collaboration data
async function syncCollaborationData() {
  try {
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'SYNC_COLLABORATION',
        payload: { timestamp: Date.now() }
      });
    });
  } catch (error) {
    console.error('[SW] Failed to sync collaboration data:', error);
  }
}

// Push notification handler
self.addEventListener('push', event => {
  console.log('[SW] Push notification received:', event);

  const options = {
    body: 'New collaboration activity in ARTIFACTOR',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    tag: 'artifactor-notification',
    renotify: true,
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/icons/action-view.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/icons/action-dismiss.png'
      }
    ],
    data: {
      url: '/dashboard'
    }
  };

  if (event.data) {
    try {
      const payload = event.data.json();
      options.body = payload.message || options.body;
      options.data.url = payload.url || options.data.url;
    } catch (error) {
      console.error('[SW] Failed to parse push payload:', error);
    }
  }

  event.waitUntil(
    self.registration.showNotification('ARTIFACTOR v3.0', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
  console.log('[SW] Notification clicked:', event);

  event.notification.close();

  if (event.action === 'dismiss') {
    return;
  }

  const url = event.notification.data?.url || '/dashboard';

  event.waitUntil(
    self.clients.matchAll().then(clients => {
      // Try to focus existing window
      for (const client of clients) {
        if (client.url.includes(url) && 'focus' in client) {
          return client.focus();
        }
      }

      // Open new window if none exists
      if (self.clients.openWindow) {
        return self.clients.openWindow(url);
      }
    })
  );
});

// IndexedDB utilities for offline storage
function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('artifactor-offline', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = event => {
      const db = event.target.result;

      if (!db.objectStoreNames.contains('uploads')) {
        const uploadsStore = db.createObjectStore('uploads', { keyPath: 'id', autoIncrement: true });
        uploadsStore.createIndex('timestamp', 'timestamp');
      }

      if (!db.objectStoreNames.contains('collaboration')) {
        const collaborationStore = db.createObjectStore('collaboration', { keyPath: 'id', autoIncrement: true });
        collaborationStore.createIndex('timestamp', 'timestamp');
      }
    };
  });
}

function getOfflineUploads(db) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['uploads'], 'readonly');
    const store = transaction.objectStore('uploads');
    const request = store.getAll();

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

function removeOfflineUpload(db, id) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['uploads'], 'readwrite');
    const store = transaction.objectStore('uploads');
    const request = store.delete(id);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

console.log('[SW] Service worker script loaded successfully');