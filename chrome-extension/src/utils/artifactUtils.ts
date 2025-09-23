// ARTIFACTOR Chrome Extension - Artifact Utility Functions
import { ArtifactType, FILE_TYPE_PATTERNS } from '../types';

/**
 * Generate a unique artifact ID
 */
export function generateArtifactId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substr(2, 5);
  return `artifact_${timestamp}_${random}`;
}

/**
 * Detect artifact type from content and element
 */
export function detectArtifactType(content: string, element?: Element): ArtifactType {
  // Check element classes and attributes first
  if (element) {
    const classList = Array.from(element.classList).join(' ').toLowerCase();
    const tagName = element.tagName.toLowerCase();

    // Check for language-specific classes
    if (classList.includes('javascript') || classList.includes('js')) return 'javascript';
    if (classList.includes('typescript') || classList.includes('ts')) return 'typescript';
    if (classList.includes('python') || classList.includes('py')) return 'python';
    if (classList.includes('html')) return 'html';
    if (classList.includes('css')) return 'css';
    if (classList.includes('json')) return 'json';
    if (classList.includes('xml')) return 'xml';
    if (classList.includes('markdown') || classList.includes('md')) return 'markdown';
    if (classList.includes('svg')) return 'svg';

    // Check tag names
    if (tagName === 'svg') return 'svg';
    if (tagName === 'style') return 'css';
    if (tagName === 'script') return 'javascript';
  }

  // Analyze content patterns
  const trimmedContent = content.trim();
  const lowerContent = content.toLowerCase();

  // HTML detection
  if (trimmedContent.startsWith('<!DOCTYPE html') ||
      trimmedContent.startsWith('<html') ||
      (trimmedContent.includes('<') && trimmedContent.includes('</') && lowerContent.includes('html'))) {
    return 'html';
  }

  // SVG detection
  if (trimmedContent.startsWith('<svg') || lowerContent.includes('<svg')) {
    return 'svg';
  }

  // XML detection
  if (trimmedContent.startsWith('<?xml') ||
      (trimmedContent.startsWith('<') && !lowerContent.includes('html'))) {
    return 'xml';
  }

  // JSON detection
  try {
    if ((trimmedContent.startsWith('{') && trimmedContent.endsWith('}')) ||
        (trimmedContent.startsWith('[') && trimmedContent.endsWith(']'))) {
      JSON.parse(trimmedContent);
      return 'json';
    }
  } catch {
    // Not valid JSON
  }

  // CSS detection
  if (lowerContent.includes('css') ||
      /\{[^}]*[a-z-]+\s*:\s*[^}]*\}/.test(content) ||
      /\.[a-z][\w-]*\s*\{/.test(content)) {
    return 'css';
  }

  // JavaScript/TypeScript detection
  if (lowerContent.includes('function') ||
      lowerContent.includes('const ') ||
      lowerContent.includes('let ') ||
      lowerContent.includes('var ') ||
      lowerContent.includes('class ') ||
      lowerContent.includes('import ') ||
      lowerContent.includes('export ')) {

    // TypeScript specific patterns
    if (lowerContent.includes('interface ') ||
        lowerContent.includes('type ') ||
        content.includes(': string') ||
        content.includes(': number') ||
        content.includes(': boolean')) {
      return 'typescript';
    }

    return 'javascript';
  }

  // Python detection
  if (lowerContent.includes('def ') ||
      lowerContent.includes('class ') ||
      lowerContent.includes('import ') ||
      trimmedContent.startsWith('#!') && lowerContent.includes('python') ||
      /^\s*from\s+\w+\s+import/.test(content)) {
    return 'python';
  }

  // Markdown detection
  if (content.includes('# ') ||
      content.includes('## ') ||
      content.includes('### ') ||
      content.includes('```') ||
      content.includes('[](') ||
      content.includes('**') ||
      content.includes('*') && content.includes('\n')) {
    return 'markdown';
  }

  // Code detection (generic)
  if (element?.tagName.toLowerCase() === 'code' ||
      element?.tagName.toLowerCase() === 'pre' ||
      element?.closest('pre, code') ||
      content.includes('{') && content.includes('}') ||
      content.includes('(') && content.includes(')') ||
      content.split('\n').length > 5 && content.includes(';')) {
    return 'code';
  }

  // Default to text for everything else
  return 'text';
}

/**
 * Sanitize content for safe storage and transmission
 */
export function sanitizeContent(content: string): string {
  if (!content) return '';

  // Remove null bytes and other control characters except newlines and tabs
  let sanitized = content.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');

  // Normalize line endings
  sanitized = sanitized.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

  // Trim excessive whitespace while preserving intentional formatting
  sanitized = sanitized.replace(/\n{4,}/g, '\n\n\n');

  // Remove leading/trailing whitespace
  sanitized = sanitized.trim();

  return sanitized;
}

/**
 * Get file extension for artifact type
 */
export function getFileExtension(type: ArtifactType, language?: string): string {
  const extensions: Record<ArtifactType, string> = {
    text: 'txt',
    code: language ? getLanguageExtension(language) : 'txt',
    html: 'html',
    css: 'css',
    javascript: 'js',
    typescript: 'ts',
    python: 'py',
    json: 'json',
    xml: 'xml',
    markdown: 'md',
    svg: 'svg',
    other: 'txt',
  };

  return extensions[type] || 'txt';
}

/**
 * Get file extension for programming language
 */
function getLanguageExtension(language: string): string {
  const langExtensions: Record<string, string> = {
    javascript: 'js',
    typescript: 'ts',
    python: 'py',
    java: 'java',
    cpp: 'cpp',
    'c++': 'cpp',
    c: 'c',
    csharp: 'cs',
    'c#': 'cs',
    php: 'php',
    ruby: 'rb',
    go: 'go',
    rust: 'rs',
    swift: 'swift',
    kotlin: 'kt',
    scala: 'scala',
    r: 'r',
    matlab: 'm',
    sql: 'sql',
    shell: 'sh',
    bash: 'bash',
    powershell: 'ps1',
    yaml: 'yml',
    toml: 'toml',
    ini: 'ini',
    dockerfile: 'dockerfile',
  };

  return langExtensions[language.toLowerCase()] || 'txt';
}

/**
 * Generate filename for artifact
 */
export function generateFilename(
  title: string,
  type: ArtifactType,
  timestamp: number,
  language?: string,
  naming: 'original' | 'timestamp' | 'conversation' = 'conversation'
): string {
  const extension = getFileExtension(type, language);
  const date = new Date(timestamp);

  let baseName = '';

  switch (naming) {
    case 'timestamp':
      baseName = `artifact_${date.toISOString().replace(/[:.]/g, '-')}`;
      break;

    case 'original':
      baseName = sanitizeFilename(title);
      break;

    case 'conversation':
    default:
      const sanitizedTitle = sanitizeFilename(title);
      const timeStr = date.toISOString().substring(11, 19).replace(/:/g, '-');
      baseName = `${sanitizedTitle}_${timeStr}`;
      break;
  }

  return `${baseName}.${extension}`;
}

/**
 * Sanitize filename for file system compatibility
 */
function sanitizeFilename(filename: string): string {
  return filename
    .replace(/[<>:"/\\|?*\x00-\x1f]/g, '_') // Replace invalid characters
    .replace(/\s+/g, '_') // Replace spaces with underscores
    .replace(/_+/g, '_') // Replace multiple underscores with single
    .replace(/^_|_$/g, '') // Remove leading/trailing underscores
    .substring(0, 100); // Limit length
}

/**
 * Calculate content hash for deduplication
 */
export async function calculateContentHash(content: string): Promise<string> {
  if (!crypto.subtle) {
    // Fallback for environments without crypto.subtle
    return btoa(content).substring(0, 16);
  }

  try {
    const encoder = new TextEncoder();
    const data = encoder.encode(content);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').substring(0, 16);
  } catch (error) {
    console.warn('Failed to calculate hash:', error);
    return btoa(content.substring(0, 100)).substring(0, 16);
  }
}

/**
 * Estimate download size for artifact
 */
export function estimateDownloadSize(content: string): number {
  // Rough estimate including metadata and encoding overhead
  const textSize = new TextEncoder().encode(content).length;
  return Math.ceil(textSize * 1.2); // Add 20% overhead
}

/**
 * Validate artifact content
 */
export function validateArtifactContent(content: string, type: ArtifactType): boolean {
  if (!content || content.length === 0) return false;
  if (content.length > 10 * 1024 * 1024) return false; // Max 10MB

  // Type-specific validation
  switch (type) {
    case 'json':
      try {
        JSON.parse(content);
        return true;
      } catch {
        return false;
      }

    case 'html':
      return content.toLowerCase().includes('<html') ||
             content.toLowerCase().includes('<!doctype') ||
             (content.includes('<') && content.includes('>'));

    case 'svg':
      return content.toLowerCase().includes('<svg');

    case 'xml':
      return content.trim().startsWith('<?xml') ||
             (content.includes('<') && content.includes('</'));

    default:
      return true;
  }
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Debounce function for performance optimization
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T {
  let timeoutId: number;

  return ((...args: any[]) => {
    clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => func.apply(null, args), delay);
  }) as T;
}