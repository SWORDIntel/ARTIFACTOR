// ARTIFACTOR Chrome Extension Types

export interface ClaudeArtifact {
  id: string;
  title: string;
  content: string;
  type: ArtifactType;
  language?: string;
  timestamp: number;
  conversationId: string;
  url: string;
  size: number;
  checksum?: string;
}

export type ArtifactType =
  | 'text'
  | 'code'
  | 'html'
  | 'svg'
  | 'markdown'
  | 'json'
  | 'xml'
  | 'css'
  | 'javascript'
  | 'typescript'
  | 'python'
  | 'other';

export interface ConversationInfo {
  id: string;
  title: string;
  url: string;
  timestamp: number;
  artifactCount: number;
}

export interface DownloadProgress {
  artifactId: string;
  status: 'queued' | 'downloading' | 'completed' | 'failed';
  progress: number;
  error?: string;
}

export interface ExtensionSettings {
  // ARTIFACTOR Backend Configuration
  backendUrl: string;
  apiKey?: string;
  autoSync: boolean;

  // Download Preferences
  downloadFolder: string;
  autoDownload: boolean;
  fileNaming: 'original' | 'timestamp' | 'conversation';

  // Detection Settings
  autoDetect: boolean;
  highlightArtifacts: boolean;
  showNotifications: boolean;

  // UI Preferences
  darkTheme: boolean;
  compactMode: boolean;
  showBadges: boolean;
}

export interface ExtensionState {
  isActive: boolean;
  currentPage: 'claude' | 'other';
  detectedArtifacts: ClaudeArtifact[];
  downloadQueue: DownloadProgress[];
  settings: ExtensionSettings;
  backendConnected: boolean;
}

export interface BackendResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: number;
}

export interface BackendArtifactRequest {
  url: string;
  conversationId: string;
  artifacts: ClaudeArtifact[];
  settings: Partial<ExtensionSettings>;
}

// Message types for communication between extension components
export type MessageType =
  | 'DETECT_ARTIFACTS'
  | 'DOWNLOAD_ARTIFACT'
  | 'UPDATE_SETTINGS'
  | 'GET_STATE'
  | 'SYNC_BACKEND'
  | 'HIGHLIGHT_TOGGLE'
  | 'NOTIFICATION';

export interface ExtensionMessage<T = any> {
  type: MessageType;
  payload?: T;
  timestamp: number;
  source: 'content' | 'popup' | 'background' | 'options';
}

// Content script detection result
export interface ArtifactDetectionResult {
  artifacts: ClaudeArtifact[];
  conversationInfo: ConversationInfo;
  pageUrl: string;
  detectionTime: number;
}

// Popup component props
export interface PopupComponentProps {
  artifacts: ClaudeArtifact[];
  downloadProgress: DownloadProgress[];
  settings: ExtensionSettings;
  onDownload: (artifactId: string) => void;
  onDownloadAll: () => void;
  onSettingsChange: (settings: Partial<ExtensionSettings>) => void;
  onRefresh: () => void;
}

// Options page component props
export interface OptionsComponentProps {
  settings: ExtensionSettings;
  onSettingsChange: (settings: Partial<ExtensionSettings>) => void;
  onTestConnection: () => Promise<boolean>;
  onResetSettings: () => void;
}

// Chrome storage data structure
export interface ChromeStorageData {
  settings: ExtensionSettings;
  recentArtifacts: ClaudeArtifact[];
  downloadHistory: DownloadProgress[];
  lastSync: number;
}

// Default settings
export const DEFAULT_SETTINGS: ExtensionSettings = {
  backendUrl: 'http://localhost:8000',
  autoSync: true,
  downloadFolder: 'Downloads/ARTIFACTOR',
  autoDownload: false,
  fileNaming: 'conversation',
  autoDetect: true,
  highlightArtifacts: true,
  showNotifications: true,
  darkTheme: true,
  compactMode: false,
  showBadges: true,
};

// File type detection patterns
export const FILE_TYPE_PATTERNS: Record<string, RegExp[]> = {
  javascript: [/\.js$/, /javascript/i, /^\/\/ JavaScript/i],
  typescript: [/\.ts$/, /\.tsx$/, /typescript/i, /^\/\/ TypeScript/i],
  python: [/\.py$/, /python/i, /^# Python/i, /^#!.*python/i],
  html: [/\.html?$/, /html/i, /^<!DOCTYPE html/i, /^<html/i],
  css: [/\.css$/, /css/i, /^\/\* CSS/i],
  json: [/\.json$/, /^{.*}$/s, /application\/json/i],
  xml: [/\.xml$/, /^<\?xml/i, /application\/xml/i],
  markdown: [/\.md$/, /markdown/i, /^# /m],
  svg: [/\.svg$/, /^<svg/i, /image\/svg/i],
};

// Utility type for Chrome API responses
export type ChromeRuntimeResponse<T = any> = {
  success: boolean;
  data?: T;
  error?: string;
};