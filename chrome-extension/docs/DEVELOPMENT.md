# ARTIFACTOR Chrome Extension - Development Guide

## 🏗️ Development Setup

### Prerequisites
- Node.js 16+ and npm
- Chrome/Chromium browser
- ARTIFACTOR backend running (optional for testing)

### Initial Setup
```bash
cd chrome-extension
npm install
npm run dev  # Start development build with watch
```

### Loading Extension in Chrome
1. Open `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked"
4. Select the `chrome-extension/dist` directory
5. Extension should appear in toolbar

## 🔧 Development Workflow

### File Structure
```
src/
├── background/         # Service worker for background tasks
│   └── index.ts       # Main background script
├── content/           # Content scripts injected into Claude.ai
│   ├── index.ts      # Main content script
│   └── content.css   # Injected styles
├── pages/            # Extension UI pages
│   ├── popup/        # Extension popup (React)
│   └── options/      # Settings page (React)
├── styles/           # Shared CSS
│   └── dark-theme.css # ARTIFACTOR dark theme
├── types/            # TypeScript definitions
│   └── index.ts      # Shared types
└── utils/            # Utility functions
    └── artifactUtils.ts # Artifact processing
```

### Key Components

#### Content Script (`src/content/index.ts`)
- **Purpose**: Detects artifacts on Claude.ai pages
- **Features**: DOM monitoring, artifact highlighting, download triggers
- **Communication**: Sends messages to background script

#### Background Script (`src/background/index.ts`)
- **Purpose**: Coordinates downloads and backend sync
- **Features**: Chrome APIs, state management, backend communication
- **Lifecycle**: Persistent service worker

#### Popup (`src/pages/popup/PopupApp.tsx`)
- **Purpose**: Main user interface
- **Features**: Artifact list, batch downloads, settings access
- **Framework**: React with dark theme

#### Options (`src/pages/options/OptionsApp.tsx`)
- **Purpose**: Extension configuration
- **Features**: Backend setup, download preferences, UI settings
- **Framework**: React with comprehensive settings

## 🎨 Dark Theme Development

### Color Variables
The extension uses CSS custom properties matching ARTIFACTOR desktop:

```css
:root {
  --bg-primary: #2B2B2B;
  --bg-secondary: #363636;
  --text-primary: #FFFFFF;
  --text-secondary: #CCCCCC;
  --accent-blue: #0078D4;
  /* ... see src/styles/dark-theme.css for complete palette */
}
```

### Component Styling
- Use `artifactor-*` CSS classes for consistency
- Follow existing component patterns
- Ensure accessibility with proper contrast ratios
- Test in both light and dark Chrome themes

## 🔄 Message Passing

### Communication Flow
```
Content Script → Background Script → Popup/Options
```

### Message Types
```typescript
type MessageType =
  | 'DETECT_ARTIFACTS'     // Content → Background
  | 'DOWNLOAD_ARTIFACT'    // Popup → Background
  | 'UPDATE_SETTINGS'      // Options → Background
  | 'GET_STATE'           // Popup → Background
  | 'SYNC_BACKEND'        // Any → Background
```

### Example Usage
```typescript
// Send message from popup to background
const response = await chrome.runtime.sendMessage({
  type: 'DOWNLOAD_ARTIFACT',
  payload: { artifactId: 'abc123' },
  timestamp: Date.now(),
  source: 'popup'
});
```

## 🧪 Testing

### Manual Testing
1. **Artifact Detection**: Visit Claude.ai, create code/content, verify highlighting
2. **Downloads**: Test single and batch downloads
3. **Settings**: Modify preferences, ensure persistence
4. **Backend Sync**: Configure backend, test connection

### Debugging
- **Content Script**: Chrome DevTools → Console (on Claude.ai page)
- **Background Script**: `chrome://extensions/` → Extension details → "service worker"
- **Popup/Options**: Right-click extension → "Inspect popup"

### Common Test Cases
```typescript
// Test artifact detection
await chrome.tabs.sendMessage(tabId, {
  type: 'DETECT_ARTIFACTS'
});

// Test download functionality
await chrome.runtime.sendMessage({
  type: 'DOWNLOAD_ARTIFACT',
  payload: { artifactId: 'test-id' }
});

// Test settings persistence
await chrome.storage.sync.set({ settings: testSettings });
```

## 🔌 Backend Integration

### API Endpoints
```typescript
// Health check
GET ${backendUrl}/health

// Process artifacts
POST ${backendUrl}/api/artifacts/process
{
  url: string,
  conversationId: string,
  artifacts: ClaudeArtifact[],
  settings: ExtensionSettings
}

// Sync data
POST ${backendUrl}/api/artifacts/sync
{
  artifacts: ClaudeArtifact[],
  settings: ExtensionSettings
}
```

### Development Backend
For testing without full ARTIFACTOR backend:

```javascript
// Simple test server
const express = require('express');
const app = express();

app.use(express.json());
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', '*');
  next();
});

app.get('/health', (req, res) => {
  res.json({ success: true, status: 'ok' });
});

app.post('/api/artifacts/*', (req, res) => {
  console.log('Received:', req.body);
  res.json({ success: true, data: req.body });
});

app.listen(8000, () => {
  console.log('Test backend running on http://localhost:8000');
});
```

## 📦 Build Process

### Development Build
```bash
npm run dev     # Watch mode for development
```

### Production Build
```bash
npm run build   # Optimized production build
```

### Extension Packaging
```bash
npm run package # Creates .zip for Chrome Web Store
```

### Build Configuration
- **Webpack**: Handles TypeScript, React, CSS bundling
- **Target**: Chrome Manifest V3
- **Output**: `dist/` directory with all assets

## 🚀 Deployment

### Chrome Web Store
1. **Build**: `npm run build`
2. **Package**: `npm run package`
3. **Upload**: Submit to Chrome Web Store Developer Dashboard
4. **Review**: Wait for Google review (1-3 business days)

### Enterprise Deployment
1. **Build**: Create production build
2. **Sign**: Use enterprise certificates if required
3. **Distribute**: Via enterprise policy or .crx file

## 🐛 Debugging Common Issues

### Extension Not Loading
- Check manifest.json syntax
- Verify all files exist in dist/
- Check Chrome extensions developer mode

### Content Script Not Working
- Verify Claude.ai URL patterns in manifest
- Check for JavaScript errors in console
- Ensure proper permissions

### Background Script Issues
- Check service worker in extensions page
- Verify message passing syntax
- Debug with background script inspector

### UI Not Displaying Correctly
- Check CSS class names and inheritance
- Verify React component mounting
- Test responsive design at different sizes

## 📚 Resources

### Chrome Extension APIs
- [Chrome Extensions API Reference](https://developer.chrome.com/docs/extensions/reference/)
- [Manifest V3 Migration Guide](https://developer.chrome.com/docs/extensions/migrating/)
- [Content Scripts Guide](https://developer.chrome.com/docs/extensions/mv3/content_scripts/)

### Development Tools
- [Chrome Extension CLI](https://github.com/dutiyesh/chrome-extension-cli)
- [Extension Reloader](https://chrome.google.com/webstore/detail/extensions-reloader/fimgfedafeadlieiabdeeaodndnlbhid)
- [React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)

### TypeScript & React
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React Documentation](https://reactjs.org/docs/)
- [Chrome Types](https://www.npmjs.com/package/@types/chrome)

---

**Happy Coding!** 🚀

*For questions or issues, contact: ARTIFACTOR@swordintelligence.airforce*