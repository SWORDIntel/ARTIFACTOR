// ARTIFACTOR Chrome Extension - Options/Settings Page
import React, { useState, useEffect } from 'react';
import {
  ExtensionSettings,
  ExtensionMessage,
  DEFAULT_SETTINGS,
  ChromeStorageData
} from '../../types';

const OptionsApp: React.FC = () => {
  const [settings, setSettings] = useState<ExtensionSettings>(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [connectionTesting, setConnectionTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'connected' | 'failed'>('unknown');
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const result = await chrome.storage.sync.get(['settings']);
      setSettings({ ...DEFAULT_SETTINGS, ...result.settings });
    } catch (error) {
      console.error('Error loading settings:', error);
      showMessage('error', 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async (newSettings: ExtensionSettings) => {
    try {
      setSaving(true);
      await chrome.storage.sync.set({ settings: newSettings });

      // Notify background script
      chrome.runtime.sendMessage({
        type: 'UPDATE_SETTINGS',
        payload: newSettings,
        timestamp: Date.now(),
        source: 'options'
      } as ExtensionMessage);

      setSettings(newSettings);
      showMessage('success', 'Settings saved successfully');
    } catch (error) {
      console.error('Error saving settings:', error);
      showMessage('error', 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    if (!settings.backendUrl) {
      showMessage('error', 'Please enter a backend URL first');
      return;
    }

    try {
      setConnectionTesting(true);
      setConnectionStatus('unknown');

      const url = `${settings.backendUrl}/health`;
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          ...(settings.apiKey && {
            'Authorization': `Bearer ${settings.apiKey}`
          })
        },
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });

      if (response.ok) {
        setConnectionStatus('connected');
        showMessage('success', 'Successfully connected to ARTIFACTOR backend');
      } else {
        setConnectionStatus('failed');
        showMessage('error', `Connection failed: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('Connection test error:', error);
      setConnectionStatus('failed');
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      showMessage('error', `Connection failed: ${errorMessage}`);
    } finally {
      setConnectionTesting(false);
    }
  };

  const resetSettings = async () => {
    if (confirm('Are you sure you want to reset all settings to defaults? This cannot be undone.')) {
      await saveSettings(DEFAULT_SETTINGS);
      setConnectionStatus('unknown');
      showMessage('info', 'Settings reset to defaults');
    }
  };

  const showMessage = (type: 'success' | 'error' | 'info', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleInputChange = (key: keyof ExtensionSettings, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
  };

  const handleSave = () => {
    saveSettings(settings);
  };

  if (loading) {
    return (
      <div className="artifactor-container" style={{ margin: '20px auto', maxWidth: '800px' }}>
        <div className="artifactor-header">
          🚀 ARTIFACTOR - Extension Settings
        </div>
        <div className="artifactor-content">
          <p>Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', padding: '20px', backgroundColor: 'var(--bg-primary)' }}>
      <div className="artifactor-container" style={{ margin: '0 auto', maxWidth: '800px' }}>
        {/* Header */}
        <div className="artifactor-header">
          <div className="artifactor-flex artifactor-flex-between">
            <span>🚀 ARTIFACTOR - Extension Settings</span>
            <span style={{ fontSize: '14px', fontWeight: 'normal' }}>v1.0.0</span>
          </div>
        </div>

        <div className="artifactor-content">
          {/* Status Message */}
          {message && (
            <div className={`artifactor-notification ${message.type} artifactor-mb-lg`}>
              <span>
                {message.type === 'success' && '✅'}
                {message.type === 'error' && '❌'}
                {message.type === 'info' && 'ℹ️'}
              </span>
              <span>{message.text}</span>
              <button
                onClick={() => setMessage(null)}
                style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>
          )}

          {/* Backend Configuration */}
          <div className="artifactor-card artifactor-mb-lg">
            <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>
              🔗 ARTIFACTOR Backend Integration
            </h3>

            <div className="artifactor-flex artifactor-flex-column artifactor-gap-md">
              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>
                  Backend URL
                </label>
                <input
                  type="url"
                  className="artifactor-input"
                  value={settings.backendUrl}
                  onChange={(e) => handleInputChange('backendUrl', e.target.value)}
                  placeholder="http://localhost:8000"
                  style={{ width: '100%' }}
                />
                <small style={{ color: 'var(--text-secondary)' }}>
                  URL of your ARTIFACTOR backend server
                </small>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>
                  API Key (Optional)
                </label>
                <input
                  type="password"
                  className="artifactor-input"
                  value={settings.apiKey || ''}
                  onChange={(e) => handleInputChange('apiKey', e.target.value)}
                  placeholder="Enter API key if required"
                  style={{ width: '100%' }}
                />
                <small style={{ color: 'var(--text-secondary)' }}>
                  Leave empty if your backend doesn't require authentication
                </small>
              </div>

              <div className="artifactor-flex artifactor-gap-sm">
                <button
                  className="artifactor-button primary"
                  onClick={testConnection}
                  disabled={connectionTesting || !settings.backendUrl}
                >
                  {connectionTesting ? '🔄 Testing...' : '🔍 Test Connection'}
                </button>
                {connectionStatus !== 'unknown' && (
                  <div className={`artifactor-badge ${connectionStatus === 'connected' ? 'success' : 'error'}`}>
                    {connectionStatus === 'connected' ? '✅ CONNECTED' : '❌ FAILED'}
                  </div>
                )}
              </div>

              <label className="artifactor-flex artifactor-flex-center artifactor-gap-xs" style={{ cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  className="artifactor-checkbox"
                  checked={settings.autoSync}
                  onChange={(e) => handleInputChange('autoSync', e.target.checked)}
                />
                <span>Automatically sync artifacts with backend</span>
              </label>
            </div>
          </div>

          {/* Download Preferences */}
          <div className="artifactor-card artifactor-mb-lg">
            <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>
              📥 Download Preferences
            </h3>

            <div className="artifactor-flex artifactor-flex-column artifactor-gap-md">
              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>
                  Download Folder
                </label>
                <input
                  type="text"
                  className="artifactor-input"
                  value={settings.downloadFolder}
                  onChange={(e) => handleInputChange('downloadFolder', e.target.value)}
                  placeholder="Downloads/ARTIFACTOR"
                  style={{ width: '100%' }}
                />
                <small style={{ color: 'var(--text-secondary)' }}>
                  Relative to your default Downloads folder
                </small>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>
                  File Naming Convention
                </label>
                <select
                  className="artifactor-select"
                  value={settings.fileNaming}
                  onChange={(e) => handleInputChange('fileNaming', e.target.value as any)}
                  style={{ width: '100%' }}
                >
                  <option value="conversation">Conversation-based (title_timestamp)</option>
                  <option value="timestamp">Timestamp-based (artifact_datetime)</option>
                  <option value="original">Original title only</option>
                </select>
              </div>

              <label className="artifactor-flex artifactor-flex-center artifactor-gap-xs" style={{ cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  className="artifactor-checkbox"
                  checked={settings.autoDownload}
                  onChange={(e) => handleInputChange('autoDownload', e.target.checked)}
                />
                <span>Automatically download detected artifacts</span>
              </label>
            </div>
          </div>

          {/* Detection Settings */}
          <div className="artifactor-card artifactor-mb-lg">
            <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>
              🔍 Detection & Display Settings
            </h3>

            <div className="artifactor-flex artifactor-flex-column artifactor-gap-md">
              <label className="artifactor-flex artifactor-flex-center artifactor-gap-xs" style={{ cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  className="artifactor-checkbox"
                  checked={settings.autoDetect}
                  onChange={(e) => handleInputChange('autoDetect', e.target.checked)}
                />
                <span>Automatically detect artifacts on page load</span>
              </label>

              <label className="artifactor-flex artifactor-flex-center artifactor-gap-xs" style={{ cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  className="artifactor-checkbox"
                  checked={settings.highlightArtifacts}
                  onChange={(e) => handleInputChange('highlightArtifacts', e.target.checked)}
                />
                <span>Highlight detected artifacts on Claude.ai pages</span>
              </label>

              <label className="artifactor-flex artifactor-flex-center artifactor-gap-xs" style={{ cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  className="artifactor-checkbox"
                  checked={settings.showNotifications}
                  onChange={(e) => handleInputChange('showNotifications', e.target.checked)}
                />
                <span>Show download notifications</span>
              </label>

              <label className="artifactor-flex artifactor-flex-center artifactor-gap-xs" style={{ cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  className="artifactor-checkbox"
                  checked={settings.showBadges}
                  onChange={(e) => handleInputChange('showBadges', e.target.checked)}
                />
                <span>Show artifact count badges on extension icon</span>
              </label>
            </div>
          </div>

          {/* UI Preferences */}
          <div className="artifactor-card artifactor-mb-lg">
            <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>
              🎨 Interface Preferences
            </h3>

            <div className="artifactor-flex artifactor-flex-column artifactor-gap-md">
              <label className="artifactor-flex artifactor-flex-center artifactor-gap-xs" style={{ cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  className="artifactor-checkbox"
                  checked={settings.darkTheme}
                  onChange={(e) => handleInputChange('darkTheme', e.target.checked)}
                />
                <span>Use dark theme (matches ARTIFACTOR desktop app)</span>
              </label>

              <label className="artifactor-flex artifactor-flex-center artifactor-gap-xs" style={{ cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  className="artifactor-checkbox"
                  checked={settings.compactMode}
                  onChange={(e) => handleInputChange('compactMode', e.target.checked)}
                />
                <span>Compact popup interface</span>
              </label>
            </div>
          </div>

          {/* Storage Information */}
          <div className="artifactor-card artifactor-mb-lg">
            <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>
              💾 Storage & Data
            </h3>

            <div className="artifactor-flex artifactor-flex-column artifactor-gap-sm">
              <p style={{ margin: 0, fontSize: '14px', color: 'var(--text-secondary)' }}>
                Extension data is stored locally in your browser and synced across devices when signed into Chrome.
              </p>

              <div className="artifactor-flex artifactor-gap-sm">
                <button
                  className="artifactor-button"
                  onClick={() => {
                    chrome.storage.local.clear();
                    showMessage('info', 'Local storage cleared');
                  }}
                >
                  Clear Local Data
                </button>
                <button
                  className="artifactor-button"
                  onClick={() => {
                    chrome.downloads.showDefaultFolder();
                  }}
                >
                  Open Downloads Folder
                </button>
              </div>
            </div>
          </div>

          {/* About */}
          <div className="artifactor-card artifactor-mb-lg">
            <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>
              ℹ️ About ARTIFACTOR
            </h3>

            <div className="artifactor-flex artifactor-flex-column artifactor-gap-sm">
              <p style={{ margin: 0, fontSize: '14px', color: 'var(--text-secondary)' }}>
                ARTIFACTOR Chrome Extension v1.0.0 - Professional Claude.ai artifact management with dark theme integration.
              </p>

              <div className="artifactor-flex artifactor-gap-sm">
                <button
                  className="artifactor-button"
                  onClick={() => window.open('https://github.com/SWORDIntel/ARTIFACTOR', '_blank')}
                >
                  📖 Documentation
                </button>
                <button
                  className="artifactor-button"
                  onClick={() => window.open('https://github.com/SWORDIntel/ARTIFACTOR/issues', '_blank')}
                >
                  🐛 Report Issue
                </button>
                <button
                  className="artifactor-button"
                  onClick={() => window.open('mailto:ARTIFACTOR@swordintelligence.airforce', '_blank')}
                >
                  📧 Contact
                </button>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="artifactor-flex artifactor-gap-md">
            <button
              className="artifactor-button primary artifactor-flex-grow"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? '💾 Saving...' : '💾 Save Settings'}
            </button>
            <button
              className="artifactor-button"
              onClick={resetSettings}
            >
              🔄 Reset to Defaults
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OptionsApp;