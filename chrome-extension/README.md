# ARTIFACTOR Chrome Extension

Professional Claude.ai artifact management with dark theme integration and ARTIFACTOR backend coordination.

## 🚀 Features

### **Core Functionality**
- **Real-time Artifact Detection**: Automatically detects and highlights artifacts on Claude.ai pages
- **One-Click Downloads**: Download individual artifacts or batch download multiple artifacts
- **Smart File Organization**: Intelligent file naming and folder organization
- **ARTIFACTOR Backend Integration**: Seamless sync with ARTIFACTOR desktop application

### **Dark Theme Integration**
- **Consistent Styling**: Matches ARTIFACTOR desktop application dark theme
- **Professional UI**: Clean, modern interface with ARTIFACTOR color palette
- **Responsive Design**: Optimized for popup constraints and various screen sizes
- **Accessibility**: High contrast mode and keyboard navigation support

### **Advanced Features**
- **File Type Detection**: Automatic detection of 25+ programming languages and file types
- **Progress Tracking**: Real-time download progress with queue management
- **Notification System**: Optional desktop notifications for download status
- **Settings Sync**: Chrome sync for consistent settings across devices

## 📦 Installation

### **From Chrome Web Store** (Coming Soon)
1. Visit the Chrome Web Store
2. Search for "ARTIFACTOR"
3. Click "Add to Chrome"
4. Configure your settings

### **Development Installation**
1. Clone the ARTIFACTOR repository:
   ```bash
   git clone https://github.com/SWORDIntel/ARTIFACTOR.git
   cd ARTIFACTOR/chrome-extension
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the extension:
   ```bash
   npm run build
   ```

4. Load in Chrome:
   - Open `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `chrome-extension/dist` folder

## ⚙️ Configuration

### **Backend Integration**
1. Open extension options (right-click extension icon → Options)
2. Configure ARTIFACTOR backend URL (default: `http://localhost:8000`)
3. Add API key if required
4. Test connection to ensure proper setup

### **Download Settings**
- **Download Folder**: Customize where artifacts are saved
- **File Naming**: Choose between conversation-based, timestamp, or original naming
- **Auto-Download**: Automatically download detected artifacts

### **Detection Settings**
- **Auto-Detect**: Automatically scan pages for artifacts
- **Highlight Artifacts**: Visual highlighting of detected content
- **Show Notifications**: Desktop notifications for downloads

## 🎯 Usage

### **Basic Workflow**
1. **Navigate to Claude.ai**: Extension automatically activates on Claude.ai pages
2. **Artifact Detection**: Artifacts are highlighted with blue borders and ARTIFACTOR badges
3. **Download Options**:
   - Click the download button on individual artifacts
   - Use the extension popup for batch operations
   - Enable auto-download for hands-free operation

### **Extension Popup**
- **Status Display**: Shows current page status and artifact count
- **Artifact List**: Browse all detected artifacts with type and size information
- **Batch Actions**: Select multiple artifacts for batch download
- **Quick Settings**: Access common settings and backend sync

### **Keyboard Shortcuts**
- **Ctrl+Shift+A**: Open extension popup (configurable)
- **Ctrl+Shift+D**: Download all artifacts on current page

## 🔧 Development

### **Project Structure**
```
chrome-extension/
├── src/
│   ├── background/          # Service worker
│   ├── content/            # Content scripts
│   ├── pages/             # UI pages (popup, options)
│   ├── styles/            # Dark theme CSS
│   ├── types/             # TypeScript definitions
│   └── utils/             # Utility functions
├── assets/                # Icons and static assets
├── dist/                  # Built extension
└── manifest.json         # Extension manifest
```

### **Build Commands**
```bash
npm run dev         # Development build with watch
npm run build       # Production build
npm run clean       # Clean build directory
npm run lint        # TypeScript and ESLint checks
npm run package     # Create extension package
```

### **Architecture**

#### **Content Script**
- Injects into Claude.ai pages
- Detects artifacts using DOM analysis
- Applies visual highlights and controls
- Communicates with background script

#### **Background Service Worker**
- Coordinates downloads and backend sync
- Manages extension state and settings
- Handles Chrome API interactions
- Provides message routing between components

#### **Popup Interface**
- React-based UI with dark theme
- Real-time artifact display and management
- Batch download capabilities
- Quick access to settings and status

#### **Options Page**
- Comprehensive settings management
- Backend configuration and testing
- Storage and data management
- About and help information

## 🎨 Dark Theme

The extension uses the same dark theme as the ARTIFACTOR desktop application:

### **Color Palette**
- **Primary Background**: `#2B2B2B`
- **Secondary Background**: `#363636`
- **Text Primary**: `#FFFFFF`
- **Text Secondary**: `#CCCCCC`
- **Accent Blue**: `#0078D4`
- **Success Green**: `#107C10`
- **Error Red**: `#D13438`

### **Components**
- **Buttons**: Dark background with blue accents
- **Cards**: Rounded corners with subtle shadows
- **Inputs**: Dark styling with focus indicators
- **Badges**: Color-coded status indicators

## 🔒 Privacy & Security

### **Data Handling**
- **Local Storage**: Extension data stored locally in browser
- **No Tracking**: No analytics or user tracking
- **Optional Backend**: Backend integration is entirely optional
- **Secure Communication**: HTTPS-only backend communication

### **Permissions**
- **activeTab**: Access current Claude.ai tab for artifact detection
- **storage**: Save settings and recent artifacts
- **downloads**: Manage artifact downloads
- **scripting**: Inject content scripts for detection

## 🚀 Integration with ARTIFACTOR Backend

### **API Endpoints**
- **POST /api/artifacts/process**: Process detected artifacts
- **POST /api/artifacts/sync**: Sync extension data
- **GET /health**: Backend health check

### **Sync Features**
- **Real-time Sync**: Automatic synchronization of detected artifacts
- **Settings Sync**: Backend-side settings management
- **Download History**: Centralized download tracking
- **Multi-Device**: Consistent experience across devices

## 📱 Mobile Support

While primarily designed for desktop, the extension includes mobile optimizations:

- **Responsive Design**: Adapts to smaller screens
- **Touch Targets**: Larger buttons for touch interaction
- **Simplified UI**: Streamlined interface for mobile constraints

## 🛠️ Troubleshooting

### **Common Issues**

#### **Extension Not Detecting Artifacts**
1. Ensure you're on a Claude.ai page
2. Check that auto-detect is enabled in settings
3. Refresh the page to trigger detection
4. Verify Claude.ai hasn't changed their DOM structure

#### **Downloads Not Working**
1. Check browser download permissions
2. Verify download folder exists and is writable
3. Ensure no download blocking extensions are active
4. Clear browser cache and reload extension

#### **Backend Connection Issues**
1. Verify backend URL is correct and accessible
2. Check API key configuration if required
3. Ensure CORS is properly configured on backend
4. Test connection using the options page

### **Debug Mode**
Enable debug logging in the extension options for detailed troubleshooting information.

## 📞 Support

### **Getting Help**
- **Documentation**: https://github.com/SWORDIntel/ARTIFACTOR
- **Issues**: Report bugs via GitHub Issues
- **Email**: ARTIFACTOR@swordintelligence.airforce

### **Contributing**
1. Fork the repository
2. Create a feature branch
3. Make your changes following the coding standards
4. Submit a pull request with detailed description

## 📄 License

Open Source - see LICENSE file for details.

---

**ARTIFACTOR Chrome Extension v1.0.0**
*Making Claude.ai artifact management professional and efficient*

*Contact: ARTIFACTOR@swordintelligence.airforce*
*Organization: SWORD Intelligence - Advanced AI & Software Solutions*