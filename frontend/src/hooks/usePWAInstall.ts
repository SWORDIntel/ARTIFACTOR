import { useContext } from 'react';
import { usePWAInstall as usePWAInstallContext } from '../contexts/PWAInstallContext';

// Re-export the hook from context for convenience
export const usePWAInstall = usePWAInstallContext;