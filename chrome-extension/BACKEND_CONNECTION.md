# Chrome Extension Backend Connection Guide

**Complete guide for integrating the ARTIFACTOR Chrome Extension with the backend API**

---

## Table of Contents

- [Quick Connection Setup](#quick-connection-setup)
- [Backend Architecture](#backend-architecture)
- [API Endpoints Reference](#api-endpoints-reference)
- [Authentication Setup](#authentication-setup)
- [Extension Configuration](#extension-configuration)
- [Testing Connection](#testing-connection)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Performance Optimization](#performance-optimization)

---

## Quick Connection Setup

### Prerequisites
- ARTIFACTOR backend running (see [QUICK_START.md](../QUICK_START.md))
- Chrome Extension installed
- Network access to backend server

### Basic Configuration (Local)

**1. Start Backend:**
```bash
cd ARTIFACTOR
./start-backend start
```

**2. Configure Extension:**
```
Backend URL: http://localhost:8000
API Endpoint: /api
WebSocket: ws://localhost:8000/ws
```

**3. Test Connection:**
- Open extension options
- Click "Test Connection"
- Verify green checkmark

---

## Backend Architecture

### Service Components

```
┌─────────────────────────────────────────────────────────┐
│                 Chrome Extension                         │
│  (Content Script → Background Worker → API Client)      │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/WebSocket
                     ↓
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                 │
│  • REST API Endpoints                                    │
│  • WebSocket Server                                      │
│  • Authentication Layer                                  │
└────────────────────┬────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      ↓              ↓               ↓
┌──────────┐  ┌──────────┐  ┌──────────────┐
│PostgreSQL│  │  Redis   │  │ Agent Bridge │
│Port 5432 │  │Port 6379 │  │  Coordinator │
└──────────┘  └──────────┘  └──────────────┘
```

### Communication Flow

**1. Artifact Detection (Content Script)**
```javascript
// Detect artifacts on Claude.ai
const artifacts = detectArtifacts();

// Send to background worker
chrome.runtime.sendMessage({
  type: 'ARTIFACTS_DETECTED',
  artifacts: artifacts
});
```

**2. API Synchronization (Background Worker)**
```javascript
// Background worker syncs with backend
const response = await fetch('http://localhost:8000/api/artifacts/sync', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ artifacts })
});
```

**3. Real-time Updates (WebSocket)**
```javascript
// WebSocket for live collaboration
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  handleArtifactUpdate(update);
};
```

---

## API Endpoints Reference

### Base Configuration
```
Base URL: http://localhost:8000
API Prefix: /api
API Version: 3.0.0
```

### Health & Status

#### GET /api/health
Check backend health and connectivity.

**Request:**
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "agent_bridge": {
    "status": "active",
    "agents_online": 5
  },
  "version": "3.0.0"
}
```

**Use Case**: Extension startup health check, connection testing

---

### Authentication

#### POST /api/auth/register
Register new user account.

**Request:**
```javascript
const response = await fetch('http://localhost:8000/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: "user@example.com",
    password: "secure_password",
    email: "user@example.com"
  })
});
```

**Response:**
```json
{
  "id": "uuid-string",
  "username": "user@example.com",
  "email": "user@example.com",
  "created_at": "2025-10-11T12:00:00Z"
}
```

#### POST /api/auth/login
Authenticate and receive JWT token.

**Request:**
```javascript
const response = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    username: "user@example.com",
    password: "secure_password"
  })
});
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Extension Usage:**
```javascript
// Store token securely
chrome.storage.local.set({
  authToken: response.access_token,
  tokenExpiry: Date.now() + (response.expires_in * 1000)
});
```

#### POST /api/auth/refresh
Refresh expired JWT token.

**Request:**
```javascript
const response = await fetch('http://localhost:8000/api/auth/refresh', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${oldToken}`
  }
});
```

---

### Artifacts

#### POST /api/artifacts/upload
Upload artifact to backend.

**Request:**
```javascript
const formData = new FormData();
formData.append('file', blob, 'example.js');
formData.append('artifact_type', 'javascript');
formData.append('source_url', window.location.href);

const response = await fetch('http://localhost:8000/api/artifacts/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

**Response:**
```json
{
  "id": "artifact-uuid",
  "filename": "example.js",
  "artifact_type": "javascript",
  "size": 1024,
  "hash": "sha256:...",
  "uploaded_at": "2025-10-11T12:00:00Z",
  "classification": {
    "category": "web_development",
    "confidence": 0.95,
    "tags": ["javascript", "frontend", "react"]
  }
}
```

#### POST /api/artifacts/sync
Synchronize multiple artifacts.

**Request:**
```javascript
const response = await fetch('http://localhost:8000/api/artifacts/sync', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    artifacts: [
      {
        content: "console.log('Hello');",
        type: "javascript",
        source_url: "https://claude.ai/chat/..."
      }
    ],
    conversation_id: "claude-chat-id"
  })
});
```

**Response:**
```json
{
  "synced": 1,
  "skipped": 0,
  "errors": 0,
  "artifacts": [
    {
      "id": "artifact-uuid",
      "status": "synced"
    }
  ]
}
```

#### GET /api/artifacts
List artifacts with filtering.

**Request:**
```bash
curl "http://localhost:8000/api/artifacts?limit=10&type=javascript" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Query Parameters:**
- `limit` (int): Number of results (default: 20, max: 100)
- `offset` (int): Pagination offset
- `type` (string): Filter by artifact type
- `search` (string): Search in content/filename
- `tags` (string[]): Filter by tags
- `from_date` (ISO 8601): Start date filter
- `to_date` (ISO 8601): End date filter

**Response:**
```json
{
  "total": 42,
  "limit": 10,
  "offset": 0,
  "artifacts": [
    {
      "id": "uuid",
      "filename": "example.js",
      "type": "javascript",
      "size": 1024,
      "created_at": "2025-10-11T12:00:00Z"
    }
  ]
}
```

#### GET /api/artifacts/{id}
Get artifact details.

**Request:**
```bash
curl "http://localhost:8000/api/artifacts/artifact-uuid" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Response:**
```json
{
  "id": "artifact-uuid",
  "filename": "example.js",
  "content": "console.log('Hello World');",
  "type": "javascript",
  "size": 29,
  "hash": "sha256:abc123...",
  "tags": ["javascript", "tutorial"],
  "metadata": {
    "source": "claude.ai",
    "conversation_id": "chat-id"
  },
  "classification": {
    "category": "education",
    "confidence": 0.89
  }
}
```

#### GET /api/artifacts/{id}/download
Download artifact file.

**Request:**
```javascript
const response = await fetch(
  `http://localhost:8000/api/artifacts/${artifactId}/download`,
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

const blob = await response.blob();
const url = URL.createObjectURL(blob);
chrome.downloads.download({ url: url, filename: 'artifact.js' });
```

---

### Search & Classification

#### POST /api/search/semantic
Semantic search across artifacts.

**Request:**
```javascript
const response = await fetch('http://localhost:8000/api/search/semantic', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: "React component for user authentication",
    limit: 5,
    threshold: 0.7
  })
});
```

**Response:**
```json
{
  "results": [
    {
      "artifact_id": "uuid",
      "filename": "LoginForm.jsx",
      "similarity": 0.92,
      "excerpt": "function LoginForm() { ... }"
    }
  ],
  "total": 5,
  "query_time_ms": 45
}
```

#### POST /api/ml/classify
Classify artifact using ML.

**Request:**
```javascript
const response = await fetch('http://localhost:8000/api/ml/classify', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    content: artifactContent,
    filename: "example.js"
  })
});
```

**Response:**
```json
{
  "category": "web_development",
  "subcategory": "frontend_react",
  "confidence": 0.95,
  "tags": ["react", "jsx", "component"],
  "language": "javascript",
  "framework": "react"
}
```

---

### Collaboration

#### WebSocket: /ws
Real-time collaboration and updates.

**Connection:**
```javascript
const ws = new WebSocket(
  `ws://localhost:8000/ws?token=${authToken}`
);

ws.onopen = () => {
  console.log('Connected to ARTIFACTOR backend');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  handleRealtimeUpdate(message);
};
```

**Message Types:**
```json
{
  "type": "artifact_created",
  "data": {
    "artifact_id": "uuid",
    "filename": "new.js",
    "user": "user@example.com"
  }
}

{
  "type": "artifact_updated",
  "data": {
    "artifact_id": "uuid",
    "changes": ["content", "tags"]
  }
}

{
  "type": "user_presence",
  "data": {
    "user_id": "uuid",
    "status": "online",
    "artifact_id": "viewing-uuid"
  }
}
```

---

## Authentication Setup

### Token-Based Authentication

**1. Login Flow:**
```javascript
// Extension background script
async function login(username, password) {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username, password })
  });

  const { access_token, expires_in } = await response.json();

  // Store securely
  await chrome.storage.local.set({
    authToken: access_token,
    tokenExpiry: Date.now() + (expires_in * 1000)
  });

  return access_token;
}
```

**2. Automatic Token Refresh:**
```javascript
async function getValidToken() {
  const { authToken, tokenExpiry } = await chrome.storage.local.get([
    'authToken',
    'tokenExpiry'
  ]);

  // Refresh if expiring in < 5 minutes
  if (Date.now() > tokenExpiry - 300000) {
    return await refreshToken(authToken);
  }

  return authToken;
}

async function refreshToken(oldToken) {
  const response = await fetch('http://localhost:8000/api/auth/refresh', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${oldToken}` }
  });

  const { access_token, expires_in } = await response.json();

  await chrome.storage.local.set({
    authToken: access_token,
    tokenExpiry: Date.now() + (expires_in * 1000)
  });

  return access_token;
}
```

**3. Authenticated Requests:**
```javascript
async function apiRequest(endpoint, options = {}) {
  const token = await getValidToken();

  const response = await fetch(`http://localhost:8000${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });

  if (response.status === 401) {
    // Token invalid, re-login required
    await logout();
    throw new Error('Authentication required');
  }

  return response;
}
```

### Optional: API Key Authentication

For service accounts or CI/CD:

**Configuration:**
```javascript
// Extension options
{
  "backend_url": "http://localhost:8000",
  "api_key": "artifactor_key_abc123...",
  "auth_method": "api_key"
}
```

**Usage:**
```javascript
const response = await fetch('http://localhost:8000/api/artifacts', {
  headers: {
    'X-API-Key': apiKey
  }
});
```

---

## Extension Configuration

### Extension Options Schema

```javascript
// chrome.storage.sync
{
  // Backend Connection
  "backend_url": "http://localhost:8000",
  "api_version": "3.0",
  "auto_connect": true,
  "connection_timeout": 5000,

  // Authentication
  "auth_method": "jwt",  // or "api_key"
  "auto_login": false,
  "remember_credentials": false,

  // Sync Settings
  "auto_sync": true,
  "sync_interval": 30000,  // 30 seconds
  "sync_on_detect": true,
  "batch_size": 10,

  // Download Settings
  "auto_download": false,
  "download_folder": "ARTIFACTOR",
  "organize_by_date": true,
  "organize_by_type": true,

  // Advanced Features
  "enable_ml_classification": true,
  "enable_semantic_search": true,
  "enable_websocket": true,
  "enable_notifications": true
}
```

### Configuration UI

**Options Page HTML:**
```html
<div class="backend-config">
  <h3>Backend Connection</h3>

  <label>Backend URL</label>
  <input type="url" id="backend_url"
         placeholder="http://localhost:8000" />

  <label>Connection Timeout (ms)</label>
  <input type="number" id="connection_timeout"
         value="5000" min="1000" max="30000" />

  <button id="test-connection">Test Connection</button>
  <span id="connection-status"></span>

  <h3>Authentication</h3>

  <label>Method</label>
  <select id="auth_method">
    <option value="jwt">JWT Token</option>
    <option value="api_key">API Key</option>
  </select>

  <label>Username/Email</label>
  <input type="text" id="username" />

  <label>Password</label>
  <input type="password" id="password" />

  <button id="login">Login</button>
</div>
```

---

## Testing Connection

### Automated Tests

**1. Health Check Test:**
```javascript
async function testHealthCheck() {
  try {
    const response = await fetch('http://localhost:8000/api/health', {
      method: 'GET',
      timeout: 5000
    });

    if (response.ok) {
      const data = await response.json();
      console.log('✓ Backend healthy:', data.status);
      return true;
    }
  } catch (error) {
    console.error('✗ Health check failed:', error);
    return false;
  }
}
```

**2. Authentication Test:**
```javascript
async function testAuthentication(username, password) {
  try {
    const response = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password })
    });

    if (response.ok) {
      const { access_token } = await response.json();
      console.log('✓ Authentication successful');
      return access_token;
    }
  } catch (error) {
    console.error('✗ Authentication failed:', error);
    return null;
  }
}
```

**3. Upload Test:**
```javascript
async function testUpload(token) {
  const testContent = 'console.log("Test artifact");';
  const blob = new Blob([testContent], { type: 'text/javascript' });

  const formData = new FormData();
  formData.append('file', blob, 'test.js');

  try {
    const response = await fetch('http://localhost:8000/api/artifacts/upload', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });

    if (response.ok) {
      const data = await response.json();
      console.log('✓ Upload successful:', data.id);
      return data.id;
    }
  } catch (error) {
    console.error('✗ Upload failed:', error);
    return null;
  }
}
```

**4. WebSocket Test:**
```javascript
function testWebSocket(token) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

    ws.onopen = () => {
      console.log('✓ WebSocket connected');
      ws.close();
      resolve(true);
    };

    ws.onerror = (error) => {
      console.error('✗ WebSocket failed:', error);
      reject(error);
    };

    setTimeout(() => {
      ws.close();
      reject(new Error('WebSocket connection timeout'));
    }, 5000);
  });
}
```

### Manual Testing

**Using Browser DevTools:**
```javascript
// Open extension background page DevTools
// Chrome: chrome://extensions/ → "Inspect views: background page"

// Run tests
(async () => {
  const health = await testHealthCheck();
  const token = await testAuthentication('user@example.com', 'password');
  const artifactId = await testUpload(token);
  const wsConnected = await testWebSocket(token);

  console.log('Test Results:', {
    health,
    authenticated: !!token,
    artifactId,
    wsConnected
  });
})();
```

---

## Advanced Features

### Batch Operations

**Upload Multiple Artifacts:**
```javascript
async function uploadBatch(artifacts, token) {
  const results = [];
  const batchSize = 5;

  for (let i = 0; i < artifacts.length; i += batchSize) {
    const batch = artifacts.slice(i, i + batchSize);
    const promises = batch.map(artifact => uploadArtifact(artifact, token));
    const batchResults = await Promise.allSettled(promises);
    results.push(...batchResults);
  }

  return results;
}
```

### Background Sync

**Sync Queue with Retry:**
```javascript
class SyncQueue {
  constructor() {
    this.queue = [];
    this.processing = false;
  }

  async add(artifact) {
    this.queue.push({
      artifact,
      retries: 0,
      maxRetries: 3
    });

    if (!this.processing) {
      await this.process();
    }
  }

  async process() {
    this.processing = true;

    while (this.queue.length > 0) {
      const item = this.queue.shift();

      try {
        await this.syncArtifact(item.artifact);
      } catch (error) {
        if (item.retries < item.maxRetries) {
          item.retries++;
          this.queue.push(item);
        } else {
          console.error('Sync failed permanently:', error);
        }
      }
    }

    this.processing = false;
  }

  async syncArtifact(artifact) {
    const token = await getValidToken();
    const response = await fetch('http://localhost:8000/api/artifacts/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ artifacts: [artifact] })
    });

    if (!response.ok) {
      throw new Error(`Sync failed: ${response.status}`);
    }
  }
}

const syncQueue = new SyncQueue();
```

### Caching Strategy

**Local Cache with Backend Sync:**
```javascript
class ArtifactCache {
  constructor() {
    this.cache = new Map();
    this.syncInterval = 60000; // 1 minute
    this.startSync();
  }

  async get(artifactId) {
    // Check cache first
    if (this.cache.has(artifactId)) {
      return this.cache.get(artifactId);
    }

    // Fetch from backend
    const artifact = await this.fetchFromBackend(artifactId);
    this.cache.set(artifactId, artifact);
    return artifact;
  }

  async set(artifactId, artifact) {
    this.cache.set(artifactId, artifact);
    await this.syncToBackend(artifactId, artifact);
  }

  startSync() {
    setInterval(async () => {
      await this.syncAll();
    }, this.syncInterval);
  }

  async syncAll() {
    for (const [id, artifact] of this.cache) {
      await this.syncToBackend(id, artifact);
    }
  }
}
```

---

## Troubleshooting

### Common Issues

#### Issue: Connection Refused

**Symptoms:**
- Extension shows "Disconnected"
- API requests fail with network error
- Test connection button shows red X

**Solutions:**

1. **Verify Backend Running:**
   ```bash
   ./start-backend status
   ```

2. **Check Firewall:**
   ```bash
   sudo ufw allow 8000/tcp
   sudo systemctl reload firewall
   ```

3. **Test with curl:**
   ```bash
   curl http://localhost:8000/api/health
   ```

4. **Check Extension URL:**
   - Must be exactly `http://localhost:8000`
   - No trailing slash
   - No extra path components

---

#### Issue: CORS Errors

**Symptoms:**
- Console shows "CORS policy" errors
- Requests fail in browser but work with curl

**Solutions:**

1. **Verify CORS Configuration:**
   ```bash
   curl -H "Origin: chrome-extension://your-extension-id" \
        -H "Access-Control-Request-Method: POST" \
        -X OPTIONS http://localhost:8000/api/artifacts
   ```

2. **Check Backend Settings:**
   ```python
   # backend/config.py
   ALLOWED_ORIGINS = [
     "chrome-extension://your-extension-id",
     "http://localhost:8000"
   ]
   ```

3. **Restart Backend:**
   ```bash
   ./start-backend restart
   ```

---

#### Issue: Authentication Failures

**Symptoms:**
- 401 Unauthorized errors
- Token rejected by backend
- Login fails silently

**Solutions:**

1. **Verify Credentials:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -d "username=your@email.com" \
     -d "password=yourpassword"
   ```

2. **Check Token Storage:**
   ```javascript
   chrome.storage.local.get(['authToken', 'tokenExpiry'], (data) => {
     console.log('Token:', data.authToken?.substring(0, 20) + '...');
     console.log('Expiry:', new Date(data.tokenExpiry));
   });
   ```

3. **Clear and Re-authenticate:**
   ```javascript
   chrome.storage.local.remove(['authToken', 'tokenExpiry']);
   // Then login again
   ```

---

#### Issue: Slow Performance

**Symptoms:**
- Requests take >5 seconds
- Extension feels sluggish
- Timeouts occur frequently

**Solutions:**

1. **Check Backend Health:**
   ```bash
   ./start-backend status
   docker stats artifactor_backend
   ```

2. **Enable Compression:**
   ```javascript
   const response = await fetch(url, {
     headers: {
       'Accept-Encoding': 'gzip, deflate'
     }
   });
   ```

3. **Use Batch Operations:**
   ```javascript
   // Instead of individual uploads
   for (const artifact of artifacts) {
     await upload(artifact); // Slow
   }

   // Use batch upload
   await uploadBatch(artifacts); // Fast
   ```

4. **Implement Caching:**
   ```javascript
   // Cache frequently accessed data
   const cache = await caches.open('artifactor-v1');
   await cache.put(request, response.clone());
   ```

---

## Performance Optimization

### Request Optimization

**1. Connection Pooling:**
```javascript
class APIClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.keepAlive = true;
  }

  async fetch(endpoint, options = {}) {
    return fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      keepalive: this.keepAlive
    });
  }
}

const api = new APIClient('http://localhost:8000');
```

**2. Request Debouncing:**
```javascript
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

const debouncedSync = debounce(syncArtifacts, 1000);
```

**3. Compression:**
```javascript
// Enable gzip compression for large payloads
async function compressAndUpload(content) {
  const compressed = await gzip(content);

  const response = await fetch('http://localhost:8000/api/artifacts/upload', {
    method: 'POST',
    headers: {
      'Content-Encoding': 'gzip',
      'Content-Type': 'application/octet-stream'
    },
    body: compressed
  });
}
```

### Caching Strategy

**Multi-Level Cache:**
```javascript
class CacheManager {
  constructor() {
    this.memory = new Map();           // Level 1: Memory
    this.storage = chrome.storage.local; // Level 2: Storage
  }

  async get(key) {
    // Try memory cache first
    if (this.memory.has(key)) {
      return this.memory.get(key);
    }

    // Try storage cache
    const stored = await this.storage.get(key);
    if (stored[key]) {
      this.memory.set(key, stored[key]);
      return stored[key];
    }

    // Fetch from backend
    const data = await this.fetchFromBackend(key);
    await this.set(key, data);
    return data;
  }

  async set(key, value) {
    this.memory.set(key, value);
    await this.storage.set({ [key]: value });
  }
}
```

### WebSocket Optimization

**Reconnection with Exponential Backoff:**
```javascript
class WebSocketManager {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('Connected');
      this.reconnectDelay = 1000;
    };

    this.ws.onclose = () => {
      console.log('Disconnected, reconnecting...');
      setTimeout(() => this.connect(), this.reconnectDelay);
      this.reconnectDelay = Math.min(
        this.reconnectDelay * 2,
        this.maxReconnectDelay
      );
    };
  }
}
```

---

## Security Best Practices

### Token Security

1. **Store tokens securely:**
   ```javascript
   // Use chrome.storage.local (encrypted at rest)
   chrome.storage.local.set({ authToken: token });

   // Never use localStorage or sessionStorage
   ```

2. **Implement token rotation:**
   ```javascript
   // Refresh tokens before expiry
   if (Date.now() > tokenExpiry - 300000) {
     await refreshToken();
   }
   ```

3. **Clear tokens on logout:**
   ```javascript
   async function logout() {
     await chrome.storage.local.remove(['authToken', 'tokenExpiry']);
     // Also revoke on backend
     await fetch('http://localhost:8000/api/auth/logout', {
       method: 'POST',
       headers: { 'Authorization': `Bearer ${token}` }
     });
   }
   ```

### Request Validation

1. **Validate responses:**
   ```javascript
   async function safeAPICall(endpoint, options) {
     const response = await fetch(endpoint, options);

     if (!response.ok) {
       throw new Error(`API error: ${response.status}`);
     }

     const data = await response.json();

     // Validate response schema
     if (!isValidSchema(data)) {
       throw new Error('Invalid response schema');
     }

     return data;
   }
   ```

2. **Sanitize inputs:**
   ```javascript
   function sanitizeFilename(filename) {
     return filename.replace(/[^a-z0-9.-]/gi, '_');
   }
   ```

---

## Monitoring & Logging

### Extension Logging

```javascript
class Logger {
  constructor() {
    this.logLevel = 'info';
    this.logs = [];
  }

  log(level, message, data = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data
    };

    this.logs.push(entry);
    console[level](message, data);

    // Send critical errors to backend
    if (level === 'error') {
      this.sendToBackend(entry);
    }
  }

  async sendToBackend(entry) {
    try {
      await fetch('http://localhost:8000/api/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry)
      });
    } catch (error) {
      console.error('Failed to send log:', error);
    }
  }
}

const logger = new Logger();
```

### Performance Monitoring

```javascript
class PerformanceMonitor {
  constructor() {
    this.metrics = {};
  }

  start(operation) {
    this.metrics[operation] = performance.now();
  }

  end(operation) {
    if (this.metrics[operation]) {
      const duration = performance.now() - this.metrics[operation];
      console.log(`${operation} took ${duration.toFixed(2)}ms`);
      delete this.metrics[operation];

      // Send to backend if slow
      if (duration > 1000) {
        this.reportSlowOperation(operation, duration);
      }
    }
  }
}

const perfMonitor = new PerformanceMonitor();

// Usage
perfMonitor.start('artifact_upload');
await uploadArtifact();
perfMonitor.end('artifact_upload');
```

---

## Migration from Local Storage

If migrating from Chrome Extension's local-only storage to backend:

**1. Export Local Data:**
```javascript
async function exportLocalData() {
  const { artifacts } = await chrome.storage.local.get('artifacts');
  return artifacts || [];
}
```

**2. Upload to Backend:**
```javascript
async function migrateToBackend() {
  const localArtifacts = await exportLocalData();
  const token = await getValidToken();

  for (const artifact of localArtifacts) {
    try {
      await syncArtifact(artifact, token);
      console.log(`Migrated: ${artifact.filename}`);
    } catch (error) {
      console.error(`Failed to migrate: ${artifact.filename}`, error);
    }
  }

  console.log('Migration complete!');
}
```

---

## Getting Help

### Debug Mode

Enable detailed logging in extension options:

```javascript
// Enable debug mode
chrome.storage.local.set({ debugMode: true });

// Check logs
chrome.storage.local.get('debugMode', ({ debugMode }) => {
  if (debugMode) {
    console.log('Debug mode enabled');
  }
});
```

### Support Resources

- **API Documentation**: http://localhost:8000/docs (when running)
- **Backend Status**: `./start-backend status`
- **Backend Logs**: `./start-backend logs`
- **Extension Console**: chrome://extensions/ → "Inspect views: background page"
- **GitHub Issues**: https://github.com/SWORDIntel/ARTIFACTOR/issues
- **Email**: ARTIFACTOR@swordintelligence.airforce

---

**ARTIFACTOR Chrome Extension Backend Integration**
*Production-ready API integration for enterprise artifact management*

**Version**: 1.0.0
**Backend**: 3.0.0
**Repository**: https://github.com/SWORDIntel/ARTIFACTOR
