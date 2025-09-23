// ARTIFACTOR Chrome Extension - Background Service Worker
import {
  ClaudeArtifact,
  ExtensionMessage,
  ExtensionState,
  DownloadProgress,
  BackendResponse,
  BackendArtifactRequest,
  DEFAULT_SETTINGS,
  ChromeStorageData
} from '../types';
import { generateFilename, calculateContentHash } from '../utils/artifactUtils';

class ARTIFACTORBackground {
  private static instance: ARTIFACTORBackground;
  private state: ExtensionState;
  private downloadQueue: Map<string, DownloadProgress> = new Map();
  private backendHealthCheck: ReturnType<typeof setInterval> | null = null;

  private constructor() {
    this.state = {
      isActive: true,
      currentPage: 'other',
      detectedArtifacts: [],
      downloadQueue: [],
      settings: DEFAULT_SETTINGS,
      backendConnected: false,
    };

    this.initialize();
  }

  public static getInstance(): ARTIFACTORBackground {
    if (!ARTIFACTORBackground.instance) {
      ARTIFACTORBackground.instance = new ARTIFACTORBackground();
    }
    return ARTIFACTORBackground.instance;
  }

  private async initialize(): Promise<void> {
    console.log('ARTIFACTOR: Initializing background service worker');

    try {
      // Load settings from storage
      await this.loadSettings();

      // Setup message listeners
      this.setupMessageListeners();

      // Setup tab listeners
      this.setupTabListeners();

      // Setup storage change listeners
      this.setupStorageListeners();

      // Start backend health checks
      this.startBackendHealthCheck();

      // Setup extension icon and badge
      this.updateExtensionIcon();

      console.log('ARTIFACTOR: Background service worker initialized');

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.error('ARTIFACTOR: Error initializing background worker:', errorMessage);
    }
  }

  private setupMessageListeners(): void {
    chrome.runtime.onMessage.addListener((message: ExtensionMessage, sender, sendResponse) => {
      this.handleMessage(message, sender).then(response => {
        sendResponse(response);
      }).catch(error => {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        console.error('ARTIFACTOR: Error handling message:', errorMessage);
        sendResponse({ success: false, error: errorMessage });
      });

      // Return true to indicate async response
      return true;
    });
  }

  private async handleMessage(message: ExtensionMessage, sender: chrome.runtime.MessageSender): Promise<any> {
    switch (message.type) {
      case 'DETECT_ARTIFACTS':
        return await this.handleArtifactDetection(message.payload, sender);

      case 'DOWNLOAD_ARTIFACT':
        return await this.handleDownloadRequest(message.payload);

      case 'UPDATE_SETTINGS':
        return await this.handleSettingsUpdate(message.payload);

      case 'GET_STATE':
        return { success: true, data: this.state };

      case 'SYNC_BACKEND':
        return await this.handleBackendSync();

      default:
        return { success: false, error: 'Unknown message type' };
    }
  }

  private async handleArtifactDetection(payload: any, sender: chrome.runtime.MessageSender): Promise<any> {
    try {
      if (!payload || !Array.isArray(payload.artifacts)) {
        return { success: false, error: 'Invalid payload' };
      }

      // Update state with detected artifacts
      this.state.detectedArtifacts = payload.artifacts;
      this.state.currentPage = sender.tab?.url?.includes('claude.ai') ? 'claude' : 'other';

      // Update extension badge with artifact count
      if (sender.tab?.id) {
        const count = payload.artifacts.length;
        await chrome.action.setBadgeText({
          text: count > 0 ? count.toString() : '',
          tabId: sender.tab.id
        });

        await chrome.action.setBadgeBackgroundColor({
          color: count > 0 ? '#0078D4' : '#808080',
          tabId: sender.tab.id
        });
      }

      // Store recent artifacts
      await this.storeRecentArtifacts(payload.artifacts);

      // Auto-download if enabled
      if (this.state.settings.autoDownload && payload.artifacts.length > 0) {
        await this.downloadAllArtifacts(payload.artifacts);
      }

      // Sync with backend if enabled
      if (this.state.settings.autoSync && this.state.backendConnected) {
        await this.syncWithBackend(payload);
      }

      return { success: true, data: { artifactCount: payload.artifacts.length } };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.error('ARTIFACTOR: Error handling artifact detection:', errorMessage);
      return { success: false, error: errorMessage };
    }
  }

  private async handleDownloadRequest(payload: { artifactId?: string, artifacts?: ClaudeArtifact[] }): Promise<any> {
    try {
      if (payload.artifactId) {
        // Download single artifact
        const artifact = this.state.detectedArtifacts.find(a => a.id === payload.artifactId);
        if (!artifact) {
          return { success: false, error: 'Artifact not found' };
        }
        return await this.downloadArtifact(artifact);
      } else if (payload.artifacts) {
        // Download multiple artifacts
        return await this.downloadAllArtifacts(payload.artifacts);
      } else {
        return { success: false, error: 'No artifacts specified' };
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.error('ARTIFACTOR: Error handling download request:', errorMessage);
      return { success: false, error: errorMessage };
    }
  }

  private async downloadArtifact(artifact: ClaudeArtifact): Promise<any> {
    try {
      const progress: DownloadProgress = {
        artifactId: artifact.id,
        status: 'downloading',
        progress: 0,
      };

      this.downloadQueue.set(artifact.id, progress);
      this.updateDownloadState();

      // Generate filename
      const filename = generateFilename(
        artifact.title,
        artifact.type,
        artifact.timestamp,
        artifact.language,
        this.state.settings.fileNaming
      );

      // Create blob and download URL
      const blob = new Blob([artifact.content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);

      // Start download
      const downloadId = await chrome.downloads.download({
        url: url,
        filename: `${this.state.settings.downloadFolder}/${filename}`,
        saveAs: false,
        conflictAction: 'uniquify'
      });

      // Update progress
      progress.status = 'completed';
      progress.progress = 100;
      this.downloadQueue.set(artifact.id, progress);
      this.updateDownloadState();

      // Store download history
      await this.storeDownloadHistory(artifact, filename);

      // Show notification if enabled
      if (this.state.settings.showNotifications) {
        await this.showNotification(
          'Download Complete',
          `Downloaded: ${artifact.title}`,
          'success'
        );
      }

      // Clean up URL
      URL.revokeObjectURL(url);

      return { success: true, data: { downloadId, filename } };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.error('ARTIFACTOR: Error downloading artifact:', errorMessage);

      const progress: DownloadProgress = {
        artifactId: artifact.id,
        status: 'failed',
        progress: 0,
        error: errorMessage,
      };

      this.downloadQueue.set(artifact.id, progress);
      this.updateDownloadState();

      if (this.state.settings.showNotifications) {
        await this.showNotification(
          'Download Failed',
          `Failed to download: ${artifact.title}`,
          'error'
        );
      }

      return { success: false, error: errorMessage };
    }
  }

  private async downloadAllArtifacts(artifacts: ClaudeArtifact[]): Promise<any> {
    const results = [];

    for (const artifact of artifacts) {
      const result = await this.downloadArtifact(artifact);
      results.push(result);
    }

    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;

    if (this.state.settings.showNotifications) {
      await this.showNotification(
        'Batch Download Complete',
        `Downloaded: ${successful}, Failed: ${failed}`,
        failed > 0 ? 'warning' : 'success'
      );
    }

    return {
      success: true,
      data: {
        total: artifacts.length,
        successful,
        failed,
        results
      }
    };
  }

  private async handleSettingsUpdate(settings: any): Promise<any> {
    try {
      this.state.settings = { ...this.state.settings, ...settings };
      await this.saveSettings();

      // Restart backend health check if URL changed
      if (settings.backendUrl) {
        this.startBackendHealthCheck();
      }

      return { success: true, data: this.state.settings };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.error('ARTIFACTOR: Error updating settings:', errorMessage);
      return { success: false, error: errorMessage };
    }
  }

  private async handleBackendSync(): Promise<any> {
    try {
      if (!this.state.settings.backendUrl) {
        return { success: false, error: 'Backend URL not configured' };
      }

      const request: BackendArtifactRequest = {
        url: 'chrome-extension',
        conversationId: 'sync',
        artifacts: this.state.detectedArtifacts,
        settings: this.state.settings,
      };

      const response = await this.makeBackendRequest('/api/artifacts/sync', request);

      if (response.success) {
        this.state.backendConnected = true;
        return { success: true, data: response.data };
      } else {
        this.state.backendConnected = false;
        return { success: false, error: response.error };
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.error('ARTIFACTOR: Error syncing with backend:', errorMessage);
      this.state.backendConnected = false;
      return { success: false, error: errorMessage };
    }
  }

  private async syncWithBackend(payload: any): Promise<void> {
    try {
      if (!this.state.settings.backendUrl || !this.state.backendConnected) return;

      const request: BackendArtifactRequest = {
        url: payload.pageUrl,
        conversationId: payload.conversationInfo.id,
        artifacts: payload.artifacts,
        settings: this.state.settings,
      };

      await this.makeBackendRequest('/api/artifacts/process', request);

    } catch (error) {
      console.error('ARTIFACTOR: Error syncing with backend:', error);
      this.state.backendConnected = false;
    }
  }

  private async makeBackendRequest(endpoint: string, data: any): Promise<BackendResponse> {
    const url = `${this.state.settings.backendUrl}${endpoint}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.state.settings.apiKey && {
          'Authorization': `Bearer ${this.state.settings.apiKey}`
        })
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Backend request failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  private setupTabListeners(): void {
    // Update extension state when tabs change
    chrome.tabs.onActivated.addListener(async (activeInfo) => {
      const tab = await chrome.tabs.get(activeInfo.tabId);
      this.state.currentPage = tab.url?.includes('claude.ai') ? 'claude' : 'other';
      this.updateExtensionIcon();
    });

    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
      if (changeInfo.status === 'complete' && tab.url?.includes('claude.ai')) {
        this.state.currentPage = 'claude';
        this.updateExtensionIcon();
      }
    });
  }

  private setupStorageListeners(): void {
    chrome.storage.onChanged.addListener((changes, areaName) => {
      if (areaName === 'sync' && changes.settings) {
        this.state.settings = changes.settings.newValue || DEFAULT_SETTINGS;
      }
    });
  }

  private async loadSettings(): Promise<void> {
    try {
      const result = await chrome.storage.sync.get(['settings']);
      this.state.settings = { ...DEFAULT_SETTINGS, ...result.settings };
    } catch (error) {
      console.error('ARTIFACTOR: Error loading settings:', error);
      this.state.settings = DEFAULT_SETTINGS;
    }
  }

  private async saveSettings(): Promise<void> {
    try {
      await chrome.storage.sync.set({ settings: this.state.settings });
    } catch (error) {
      console.error('ARTIFACTOR: Error saving settings:', error);
    }
  }

  private async storeRecentArtifacts(artifacts: ClaudeArtifact[]): Promise<void> {
    try {
      const result = await chrome.storage.local.get(['recentArtifacts']);
      const recent = result.recentArtifacts || [];

      // Add new artifacts and limit to 50 most recent
      const updated = [...artifacts, ...recent]
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, 50);

      await chrome.storage.local.set({ recentArtifacts: updated });
    } catch (error) {
      console.error('ARTIFACTOR: Error storing recent artifacts:', error);
    }
  }

  private async storeDownloadHistory(artifact: ClaudeArtifact, filename: string): Promise<void> {
    try {
      const result = await chrome.storage.local.get(['downloadHistory']);
      const history = result.downloadHistory || [];

      const entry: DownloadProgress = {
        artifactId: artifact.id,
        status: 'completed',
        progress: 100,
      };

      history.unshift(entry);
      history.slice(0, 100); // Keep last 100 downloads

      await chrome.storage.local.set({ downloadHistory: history });
    } catch (error) {
      console.error('ARTIFACTOR: Error storing download history:', error);
    }
  }

  private updateDownloadState(): void {
    this.state.downloadQueue = Array.from(this.downloadQueue.values());
  }

  private async updateExtensionIcon(): Promise<void> {
    const iconPath = this.state.currentPage === 'claude' ? {
      16: 'assets/icon-16.png',
      32: 'assets/icon-32.png',
      48: 'assets/icon-48.png',
      128: 'assets/icon-128.png'
    } : {
      16: 'assets/icon-16-disabled.png',
      32: 'assets/icon-32-disabled.png',
      48: 'assets/icon-48-disabled.png',
      128: 'assets/icon-128-disabled.png'
    };

    try {
      await chrome.action.setIcon({ path: iconPath });
    } catch (error) {
      console.warn('ARTIFACTOR: Could not update icon (disabled icons not available)');
    }
  }

  private startBackendHealthCheck(): void {
    if (this.backendHealthCheck) {
      clearInterval(this.backendHealthCheck);
    }

    if (!this.state.settings.backendUrl) return;

    this.backendHealthCheck = setInterval(async () => {
      try {
        const response = await fetch(`${this.state.settings.backendUrl}/health`, {
          method: 'GET',
          headers: {
            ...(this.state.settings.apiKey && {
              'Authorization': `Bearer ${this.state.settings.apiKey}`
            })
          }
        });

        this.state.backendConnected = response.ok;

      } catch (error) {
        this.state.backendConnected = false;
      }
    }, 30000); // Check every 30 seconds

    // Initial health check
    setTimeout(() => {
      if (this.backendHealthCheck) {
        this.handleBackendSync();
      }
    }, 1000);
  }

  private async showNotification(title: string, message: string, type: 'success' | 'warning' | 'error' = 'success'): Promise<void> {
    try {
      const iconUrl = type === 'error' ? 'assets/icon-48-error.png' :
                     type === 'warning' ? 'assets/icon-48-warning.png' :
                     'assets/icon-48.png';

      await chrome.notifications.create({
        type: 'basic',
        iconUrl,
        title: `ARTIFACTOR - ${title}`,
        message,
        priority: type === 'error' ? 2 : 1,
      });
    } catch (error) {
      console.warn('ARTIFACTOR: Could not show notification:', error);
    }
  }
}

// Initialize background service worker
ARTIFACTORBackground.getInstance();

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
  console.log('ARTIFACTOR: Extension installed/updated', details);

  if (details.reason === 'install') {
    // Open options page on first install
    chrome.runtime.openOptionsPage();
  }
});

// Handle extension startup
chrome.runtime.onStartup.addListener(() => {
  console.log('ARTIFACTOR: Extension started');
  ARTIFACTORBackground.getInstance();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ARTIFACTORBackground;
}