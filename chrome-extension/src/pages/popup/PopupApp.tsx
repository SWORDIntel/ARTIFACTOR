// ARTIFACTOR Chrome Extension - Popup Application Component
import React, { useState, useEffect } from 'react';
import {
  ClaudeArtifact,
  ExtensionState,
  DownloadProgress,
  ExtensionMessage,
  DEFAULT_SETTINGS
} from '../../types';
import { formatFileSize } from '../../utils/artifactUtils';

const PopupApp: React.FC = () => {
  const [state, setState] = useState<ExtensionState>({
    isActive: false,
    currentPage: 'other',
    detectedArtifacts: [],
    downloadQueue: [],
    settings: DEFAULT_SETTINGS,
    backendConnected: false,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedArtifacts, setSelectedArtifacts] = useState<Set<string>>(new Set());

  useEffect(() => {
    initializePopup();
  }, []);

  const initializePopup = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get current state from background script
      const response = await sendMessage({ type: 'GET_STATE' });

      if (response.success) {
        setState(response.data);
      } else {
        setError(response.error || 'Failed to load extension state');
      }

      // Trigger artifact detection if on Claude.ai
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      const currentTab = tabs[0];

      if (currentTab?.url?.includes('claude.ai')) {
        await triggerArtifactDetection();
      }

    } catch (err) {
      console.error('Error initializing popup:', err);
      setError('Failed to initialize extension');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (message: Omit<ExtensionMessage, 'timestamp' | 'source'>): Promise<any> => {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({
        ...message,
        timestamp: Date.now(),
        source: 'popup'
      } as ExtensionMessage, resolve);
    });
  };

  const triggerArtifactDetection = async () => {
    try {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      const currentTab = tabs[0];

      if (currentTab?.id && currentTab.url?.includes('claude.ai')) {
        await chrome.tabs.sendMessage(currentTab.id, {
          type: 'DETECT_ARTIFACTS',
          timestamp: Date.now(),
          source: 'popup'
        } as ExtensionMessage);
      }
    } catch (err) {
      console.warn('Could not trigger artifact detection:', err);
    }
  };

  const handleDownloadArtifact = async (artifactId: string) => {
    try {
      const response = await sendMessage({
        type: 'DOWNLOAD_ARTIFACT',
        payload: { artifactId }
      });

      if (!response.success) {
        setError(response.error || 'Download failed');
      }
    } catch (err) {
      console.error('Error downloading artifact:', err);
      setError('Download failed');
    }
  };

  const handleDownloadSelected = async () => {
    try {
      const selectedArtifactList = state.detectedArtifacts.filter(a =>
        selectedArtifacts.has(a.id)
      );

      const response = await sendMessage({
        type: 'DOWNLOAD_ARTIFACT',
        payload: { artifacts: selectedArtifactList }
      });

      if (!response.success) {
        setError(response.error || 'Batch download failed');
      } else {
        setSelectedArtifacts(new Set()); // Clear selection
      }
    } catch (err) {
      console.error('Error downloading selected artifacts:', err);
      setError('Batch download failed');
    }
  };

  const handleDownloadAll = async () => {
    try {
      const response = await sendMessage({
        type: 'DOWNLOAD_ARTIFACT',
        payload: { artifacts: state.detectedArtifacts }
      });

      if (!response.success) {
        setError(response.error || 'Download all failed');
      }
    } catch (err) {
      console.error('Error downloading all artifacts:', err);
      setError('Download all failed');
    }
  };

  const handleToggleArtifactSelection = (artifactId: string) => {
    const newSelection = new Set(selectedArtifacts);
    if (newSelection.has(artifactId)) {
      newSelection.delete(artifactId);
    } else {
      newSelection.add(artifactId);
    }
    setSelectedArtifacts(newSelection);
  };

  const handleSelectAll = () => {
    if (selectedArtifacts.size === state.detectedArtifacts.length) {
      setSelectedArtifacts(new Set());
    } else {
      setSelectedArtifacts(new Set(state.detectedArtifacts.map(a => a.id)));
    }
  };

  const handleRefresh = () => {
    initializePopup();
  };

  const handleOpenOptions = () => {
    chrome.runtime.openOptionsPage();
  };

  const handleSyncBackend = async () => {
    try {
      const response = await sendMessage({ type: 'SYNC_BACKEND' });

      if (!response.success) {
        setError(response.error || 'Backend sync failed');
      }
    } catch (err) {
      console.error('Error syncing with backend:', err);
      setError('Backend sync failed');
    }
  };

  const getArtifactIcon = (type: string) => {
    const icons: Record<string, string> = {
      javascript: '🟨',
      typescript: '🔷',
      python: '🐍',
      html: '🌐',
      css: '🎨',
      json: '📄',
      xml: '📄',
      markdown: '📝',
      svg: '🖼️',
      code: '💻',
      text: '📄',
      other: '📎'
    };
    return icons[type] || icons.other;
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'downloading': return 'info';
      case 'failed': return 'error';
      default: return 'warning';
    }
  };

  if (loading) {
    return (
      <div className="artifactor-container" style={{ padding: '20px', textAlign: 'center' }}>
        <div className="artifactor-header">
          🚀 ARTIFACTOR
        </div>
        <div className="artifactor-content">
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="artifactor-container" style={{ minHeight: '500px' }}>
      {/* Header */}
      <div className="artifactor-header artifactor-flex artifactor-flex-between">
        <div className="artifactor-flex artifactor-flex-center artifactor-gap-sm">
          <span>🚀 ARTIFACTOR</span>
          {state.backendConnected && (
            <div className="artifactor-badge success" style={{ fontSize: '10px' }}>
              CONNECTED
            </div>
          )}
        </div>
        <div className="artifactor-flex artifactor-gap-xs">
          <button
            className="artifactor-button"
            onClick={handleRefresh}
            style={{ padding: '4px 8px', fontSize: '12px' }}
            title="Refresh"
          >
            🔄
          </button>
          <button
            className="artifactor-button"
            onClick={handleOpenOptions}
            style={{ padding: '4px 8px', fontSize: '12px' }}
            title="Settings"
          >
            ⚙️
          </button>
        </div>
      </div>

      <div className="artifactor-content">
        {/* Error Message */}
        {error && (
          <div className="artifactor-notification error artifactor-mb-md">
            <span>⚠️</span>
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
            >
              ✕
            </button>
          </div>
        )}

        {/* Page Status */}
        <div className="artifactor-card artifactor-mb-md">
          <div className="artifactor-flex artifactor-flex-between artifactor-mb-sm">
            <span style={{ fontWeight: '600' }}>Status</span>
            <div className={`artifactor-badge ${state.currentPage === 'claude' ? 'success' : 'warning'}`}>
              {state.currentPage === 'claude' ? 'CLAUDE.AI' : 'OTHER PAGE'}
            </div>
          </div>

          {state.currentPage !== 'claude' && (
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
              Navigate to Claude.ai to detect artifacts
            </p>
          )}

          {state.currentPage === 'claude' && (
            <div className="artifactor-flex artifactor-flex-between" style={{ fontSize: '12px' }}>
              <span>Artifacts detected: {state.detectedArtifacts.length}</span>
              <span>Downloads: {state.downloadQueue.filter(d => d.status === 'completed').length}</span>
            </div>
          )}
        </div>

        {/* Artifacts List */}
        {state.detectedArtifacts.length > 0 && (
          <div className="artifactor-card">
            <div className="artifactor-flex artifactor-flex-between artifactor-mb-md">
              <span style={{ fontWeight: '600' }}>
                Detected Artifacts ({state.detectedArtifacts.length})
              </span>
              <div className="artifactor-flex artifactor-gap-xs">
                <button
                  className="artifactor-button"
                  onClick={handleSelectAll}
                  style={{ fontSize: '11px', padding: '4px 8px' }}
                >
                  {selectedArtifacts.size === state.detectedArtifacts.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>
            </div>

            <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
              {state.detectedArtifacts.map((artifact) => (
                <div
                  key={artifact.id}
                  className="artifactor-flex artifactor-flex-between"
                  style={{
                    padding: '8px',
                    marginBottom: '4px',
                    backgroundColor: selectedArtifacts.has(artifact.id) ? 'var(--selected-bg)' : 'var(--bg-tertiary)',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                  onClick={() => handleToggleArtifactSelection(artifact.id)}
                >
                  <div className="artifactor-flex artifactor-flex-center artifactor-gap-sm">
                    <input
                      type="checkbox"
                      className="artifactor-checkbox"
                      checked={selectedArtifacts.has(artifact.id)}
                      onChange={() => handleToggleArtifactSelection(artifact.id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                    <span style={{ fontSize: '16px' }}>{getArtifactIcon(artifact.type)}</span>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: '500' }}>
                        {artifact.title.substring(0, 30)}
                        {artifact.title.length > 30 && '...'}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                        {artifact.type}
                        {artifact.language && ` (${artifact.language})`}
                        {' • '}
                        {formatFileSize(artifact.size)}
                      </div>
                    </div>
                  </div>

                  <button
                    className="artifactor-button primary"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownloadArtifact(artifact.id);
                    }}
                    style={{ fontSize: '11px', padding: '4px 8px' }}
                  >
                    📥
                  </button>
                </div>
              ))}
            </div>

            {/* Batch Actions */}
            {state.detectedArtifacts.length > 0 && (
              <div className="artifactor-flex artifactor-gap-sm artifactor-mt-md">
                <button
                  className="artifactor-button primary artifactor-flex-grow"
                  onClick={handleDownloadSelected}
                  disabled={selectedArtifacts.size === 0}
                >
                  Download Selected ({selectedArtifacts.size})
                </button>
                <button
                  className="artifactor-button"
                  onClick={handleDownloadAll}
                  style={{ flexShrink: 0 }}
                >
                  All
                </button>
              </div>
            )}
          </div>
        )}

        {/* No Artifacts Message */}
        {state.currentPage === 'claude' && state.detectedArtifacts.length === 0 && (
          <div className="artifactor-card artifactor-text-center">
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>📄</div>
            <p style={{ margin: 0, color: 'var(--text-secondary)' }}>
              No artifacts detected on this page
            </p>
            <button
              className="artifactor-button artifactor-mt-sm"
              onClick={handleRefresh}
            >
              🔄 Refresh Detection
            </button>
          </div>
        )}

        {/* Download Queue */}
        {state.downloadQueue.length > 0 && (
          <div className="artifactor-card artifactor-mt-md">
            <div style={{ fontWeight: '600', marginBottom: '8px' }}>
              Download Queue ({state.downloadQueue.length})
            </div>

            <div style={{ maxHeight: '120px', overflowY: 'auto' }}>
              {state.downloadQueue.map((download) => (
                <div
                  key={download.artifactId}
                  className="artifactor-flex artifactor-flex-between artifactor-mb-xs"
                  style={{ fontSize: '12px' }}
                >
                  <span style={{ flex: 1 }}>
                    {state.detectedArtifacts.find(a => a.id === download.artifactId)?.title || 'Unknown'}
                  </span>
                  <div className="artifactor-flex artifactor-flex-center artifactor-gap-xs">
                    <div className={`artifactor-badge ${getStatusBadgeColor(download.status)}`}>
                      {download.status.toUpperCase()}
                    </div>
                    {download.status === 'downloading' && (
                      <div className="artifactor-progress" style={{ width: '40px', height: '4px' }}>
                        <div
                          className="artifactor-progress-fill"
                          style={{ width: `${download.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Backend Integration */}
        {state.settings.backendUrl && (
          <div className="artifactor-card artifactor-mt-md">
            <div className="artifactor-flex artifactor-flex-between artifactor-mb-sm">
              <span style={{ fontWeight: '600' }}>Backend Integration</span>
              <div className={`artifactor-badge ${state.backendConnected ? 'success' : 'error'}`}>
                {state.backendConnected ? 'CONNECTED' : 'DISCONNECTED'}
              </div>
            </div>

            <div className="artifactor-flex artifactor-gap-sm">
              <button
                className="artifactor-button artifactor-flex-grow"
                onClick={handleSyncBackend}
                disabled={!state.backendConnected}
              >
                🔄 Sync Now
              </button>
              <button
                className="artifactor-button"
                onClick={handleOpenOptions}
              >
                ⚙️ Configure
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PopupApp;