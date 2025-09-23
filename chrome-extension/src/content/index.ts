// ARTIFACTOR Chrome Extension - Content Script for Claude.ai Integration
import { ClaudeArtifact, ArtifactDetectionResult, ConversationInfo, ExtensionMessage, ArtifactType } from '../types';
import { detectArtifactType, generateArtifactId, sanitizeContent } from '../utils/artifactUtils';

class ClaudeArtifactDetector {
  private static instance: ClaudeArtifactDetector;
  private observer: MutationObserver | null = null;
  private highlightStyle: HTMLStyleElement | null = null;
  private isActive: boolean = false;
  private detectedArtifacts: ClaudeArtifact[] = [];
  private lastDetectionTime: number = 0;

  // Claude.ai specific selectors (may need updates as UI changes)
  private readonly selectors = {
    artifactContainer: '[data-testid="artifact-content"], .artifact-content, [class*="artifact"]',
    messageContainer: '[data-testid="message"], .message, [class*="message"]',
    codeBlock: 'pre code, .code-block, [class*="code"]',
    conversationTitle: 'h1, [class*="title"], [data-testid="conversation-title"]',
    conversationUrl: window.location.href,
  };

  private constructor() {
    this.initializeContentScript();
  }

  public static getInstance(): ClaudeArtifactDetector {
    if (!ClaudeArtifactDetector.instance) {
      ClaudeArtifactDetector.instance = new ClaudeArtifactDetector();
    }
    return ClaudeArtifactDetector.instance;
  }

  private async initializeContentScript(): Promise<void> {
    try {
      // Wait for page to load
      if (document.readyState === 'loading') {
        await new Promise(resolve => {
          document.addEventListener('DOMContentLoaded', resolve);
        });
      }

      // Check if we're on Claude.ai
      if (!this.isClaudePage()) {
        console.log('ARTIFACTOR: Not on Claude.ai page');
        return;
      }

      console.log('ARTIFACTOR: Initializing content script on Claude.ai');

      // Setup message listener
      this.setupMessageListener();

      // Inject highlight styles
      this.injectHighlightStyles();

      // Start observing page changes
      this.startObserver();

      // Initial artifact detection
      await this.detectArtifacts();

      this.isActive = true;
      console.log('ARTIFACTOR: Content script initialized successfully');

    } catch (error) {
      console.error('ARTIFACTOR: Error initializing content script:', error);
    }
  }

  private isClaudePage(): boolean {
    return window.location.hostname.includes('claude.ai');
  }

  private setupMessageListener(): void {
    chrome.runtime.onMessage.addListener((message: ExtensionMessage, sender, sendResponse) => {
      this.handleMessage(message).then(response => {
        sendResponse(response);
      }).catch(error => {
        console.error('ARTIFACTOR: Error handling message:', error);
        sendResponse({ success: false, error: error.message });
      });

      // Return true to indicate async response
      return true;
    });
  }

  private async handleMessage(message: ExtensionMessage): Promise<any> {
    switch (message.type) {
      case 'DETECT_ARTIFACTS':
        return await this.detectArtifacts();

      case 'HIGHLIGHT_TOGGLE':
        this.toggleHighlights(message.payload?.enabled);
        return { success: true };

      case 'GET_STATE':
        return {
          success: true,
          data: {
            isActive: this.isActive,
            artifactCount: this.detectedArtifacts.length,
            lastDetection: this.lastDetectionTime,
          }
        };

      default:
        return { success: false, error: 'Unknown message type' };
    }
  }

  private injectHighlightStyles(): void {
    if (this.highlightStyle) return;

    this.highlightStyle = document.createElement('style');
    this.highlightStyle.textContent = `
      .artifactor-highlight {
        position: relative;
        border: 2px solid #0078D4 !important;
        border-radius: 8px !important;
        background-color: rgba(0, 120, 212, 0.1) !important;
        transition: all 0.3s ease;
      }

      .artifactor-highlight::before {
        content: '🚀 ARTIFACTOR';
        position: absolute;
        top: -12px;
        right: 8px;
        background: #0078D4;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        z-index: 1000;
        font-family: 'Segoe UI', sans-serif;
      }

      .artifactor-highlight:hover {
        border-color: #106ebe !important;
        background-color: rgba(0, 120, 212, 0.2) !important;
        box-shadow: 0 4px 12px rgba(0, 120, 212, 0.3);
      }

      .artifactor-download-button {
        position: absolute;
        top: 8px;
        right: 8px;
        background: #0078D4;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 12px;
        cursor: pointer;
        z-index: 1001;
        transition: background-color 0.2s ease;
      }

      .artifactor-download-button:hover {
        background: #106ebe;
      }

      .artifactor-artifact-badge {
        position: absolute;
        bottom: 8px;
        left: 8px;
        background: rgba(43, 43, 43, 0.9);
        color: #CCCCCC;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-family: monospace;
        z-index: 1001;
      }
    `;

    document.head.appendChild(this.highlightStyle);
  }

  private startObserver(): void {
    if (this.observer) return;

    this.observer = new MutationObserver((mutations) => {
      // Debounce detection to avoid excessive calls
      if (this.detectionTimeout) clearTimeout(this.detectionTimeout);
      this.detectionTimeout = setTimeout(() => {
        this.detectArtifacts();
      }, 500);
    });

    this.observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class', 'data-testid']
    });
  }

  private detectionTimeout: ReturnType<typeof setTimeout> | null = null;

  private async detectArtifacts(): Promise<ArtifactDetectionResult> {
    try {
      const artifacts: ClaudeArtifact[] = [];
      const conversationInfo = this.getConversationInfo();

      // Detect artifacts in various containers
      const artifactElements = this.findArtifactElements();

      for (const element of artifactElements) {
        const artifact = await this.extractArtifactFromElement(element, conversationInfo);
        if (artifact) {
          artifacts.push(artifact);
        }
      }

      // Update internal state
      this.detectedArtifacts = artifacts;
      this.lastDetectionTime = Date.now();

      // Apply highlights if enabled
      await this.applyHighlights(artifactElements);

      // Notify background script
      const result: ArtifactDetectionResult = {
        artifacts,
        conversationInfo,
        pageUrl: window.location.href,
        detectionTime: this.lastDetectionTime,
      };

      chrome.runtime.sendMessage({
        type: 'DETECT_ARTIFACTS',
        payload: result,
        timestamp: Date.now(),
        source: 'content'
      } as ExtensionMessage);

      return result;

    } catch (error) {
      console.error('ARTIFACTOR: Error detecting artifacts:', error);
      throw error;
    }
  }

  private findArtifactElements(): Element[] {
    const elements: Element[] = [];

    // Find artifact containers
    const artifactContainers = document.querySelectorAll(this.selectors.artifactContainer);
    elements.push(...Array.from(artifactContainers));

    // Find code blocks
    const codeBlocks = document.querySelectorAll(this.selectors.codeBlock);
    elements.push(...Array.from(codeBlocks));

    // Find message containers that might contain artifacts
    const messageContainers = document.querySelectorAll(this.selectors.messageContainer);
    for (const container of messageContainers) {
      // Look for code, pre, or other content that looks like artifacts
      const potentialArtifacts = container.querySelectorAll('pre, code, [class*="code"], [class*="artifact"]');
      elements.push(...Array.from(potentialArtifacts));
    }

    // Remove duplicates and filter out small elements
    return Array.from(new Set(elements)).filter(el => {
      const text = el.textContent?.trim() || '';
      return text.length > 50; // Minimum content length for artifacts
    });
  }

  private async extractArtifactFromElement(element: Element, conversationInfo: ConversationInfo): Promise<ClaudeArtifact | null> {
    try {
      const content = this.extractContent(element);
      if (!content || content.length < 50) return null;

      const type = detectArtifactType(content, element);
      const title = this.extractTitle(element, type);

      const artifact: ClaudeArtifact = {
        id: generateArtifactId(),
        title,
        content: sanitizeContent(content),
        type,
        language: this.detectLanguage(content, element),
        timestamp: Date.now(),
        conversationId: conversationInfo.id,
        url: window.location.href,
        size: content.length,
      };

      return artifact;

    } catch (error) {
      console.error('ARTIFACTOR: Error extracting artifact:', error);
      return null;
    }
  }

  private extractContent(element: Element): string {
    // Try to get clean text content
    let content = '';

    if (element.tagName === 'PRE' || element.tagName === 'CODE') {
      content = element.textContent || '';
    } else {
      // For other elements, try to preserve formatting
      content = element.innerHTML || element.textContent || '';
    }

    return content.trim();
  }

  private extractTitle(element: Element, type: ArtifactType): string {
    // Try to find a title from context
    let title = '';

    // Look for preceding headings or labels
    const prevElement = element.previousElementSibling;
    if (prevElement && (prevElement.tagName.match(/^H[1-6]$/) || prevElement.classList.contains('title'))) {
      title = prevElement.textContent?.trim() || '';
    }

    // Look for parent with title-like attributes
    const parent = element.closest('[data-title], [title], [aria-label]');
    if (parent && !title) {
      title = parent.getAttribute('data-title') ||
              parent.getAttribute('title') ||
              parent.getAttribute('aria-label') || '';
    }

    // Generate default title based on type
    if (!title) {
      const timestamp = new Date().toLocaleTimeString();
      title = `${type.charAt(0).toUpperCase() + type.slice(1)} Artifact ${timestamp}`;
    }

    return title;
  }

  private detectLanguage(content: string, element: Element): string | undefined {
    // Check element classes for language hints
    const classList = Array.from(element.classList);
    for (const className of classList) {
      if (className.startsWith('language-')) {
        return className.replace('language-', '');
      }
      if (className.startsWith('lang-')) {
        return className.replace('lang-', '');
      }
    }

    // Check data attributes
    const langAttr = element.getAttribute('data-language') ||
                    element.getAttribute('data-lang');
    if (langAttr) return langAttr;

    // Try to detect from content patterns
    if (content.includes('function ') && content.includes('{')) return 'javascript';
    if (content.includes('def ') && content.includes(':')) return 'python';
    if (content.includes('class ') && content.includes('extends')) return 'java';
    if (content.includes('<html') || content.includes('<!DOCTYPE')) return 'html';
    if (content.includes('SELECT ') || content.includes('FROM ')) return 'sql';

    return undefined;
  }

  private getConversationInfo(): ConversationInfo {
    // Extract conversation ID from URL
    const urlMatch = window.location.pathname.match(/\/chat\/([^\/]+)/);
    const id = urlMatch ? urlMatch[1] : 'unknown';

    // Try to get conversation title
    const titleElement = document.querySelector(this.selectors.conversationTitle);
    const title = titleElement?.textContent?.trim() || 'Untitled Conversation';

    return {
      id,
      title,
      url: window.location.href,
      timestamp: Date.now(),
      artifactCount: this.detectedArtifacts.length,
    };
  }

  private async applyHighlights(elements: Element[]): Promise<void> {
    // Remove existing highlights
    document.querySelectorAll('.artifactor-highlight').forEach(el => {
      el.classList.remove('artifactor-highlight');
      el.querySelectorAll('.artifactor-download-button, .artifactor-artifact-badge').forEach(btn => btn.remove());
    });

    // Check if highlighting is enabled
    const settings = await this.getSettings();
    if (!settings.highlightArtifacts) return;

    // Apply new highlights
    for (let i = 0; i < elements.length; i++) {
      const element = elements[i] as HTMLElement;
      const artifact = this.detectedArtifacts[i];

      if (!artifact) continue;

      element.classList.add('artifactor-highlight');

      // Add download button
      const downloadButton = document.createElement('button');
      downloadButton.className = 'artifactor-download-button';
      downloadButton.textContent = '📥 Download';
      downloadButton.onclick = (e) => {
        e.stopPropagation();
        this.downloadArtifact(artifact.id);
      };

      // Add artifact type badge
      const badge = document.createElement('div');
      badge.className = 'artifactor-artifact-badge';
      badge.textContent = `${artifact.type}${artifact.language ? ` (${artifact.language})` : ''}`;

      // Position elements
      if (element instanceof HTMLElement) {
        element.style.position = 'relative';
      }
      element.appendChild(downloadButton);
      element.appendChild(badge);
    }
  }

  private toggleHighlights(enabled: boolean): void {
    const highlights = document.querySelectorAll('.artifactor-highlight');

    if (enabled) {
      highlights.forEach(el => {
        if (el instanceof HTMLElement) {
          el.style.display = '';
        }
      });
    } else {
      highlights.forEach(el => {
        el.classList.remove('artifactor-highlight');
        el.querySelectorAll('.artifactor-download-button, .artifactor-artifact-badge').forEach(btn => btn.remove());
      });
    }
  }

  private downloadArtifact(artifactId: string): void {
    chrome.runtime.sendMessage({
      type: 'DOWNLOAD_ARTIFACT',
      payload: { artifactId },
      timestamp: Date.now(),
      source: 'content'
    } as ExtensionMessage);
  }

  private async getSettings(): Promise<any> {
    return new Promise((resolve) => {
      chrome.storage.sync.get(['settings'], (result) => {
        resolve(result.settings || { highlightArtifacts: true });
      });
    });
  }

  public destroy(): void {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }

    if (this.highlightStyle) {
      this.highlightStyle.remove();
      this.highlightStyle = null;
    }

    this.toggleHighlights(false);
    this.isActive = false;
  }
}

// Initialize the content script when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    ClaudeArtifactDetector.getInstance();
  });
} else {
  ClaudeArtifactDetector.getInstance();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  ClaudeArtifactDetector.getInstance().destroy();
});

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ClaudeArtifactDetector;
}