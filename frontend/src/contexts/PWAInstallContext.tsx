import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

interface PWAInstallContextType {
  isInstallable: boolean;
  isInstalled: boolean;
  installApp: () => Promise<void>;
  dismissInstallPrompt: () => void;
  showInstallBanner: boolean;
  isStandalone: boolean;
  supportsPWA: boolean;
}

const PWAInstallContext = createContext<PWAInstallContextType | undefined>(undefined);

interface PWAInstallProviderProps {
  children: ReactNode;
}

export const PWAInstallProvider: React.FC<PWAInstallProviderProps> = ({ children }) => {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [showInstallBanner, setShowInstallBanner] = useState(false);

  // Check if app is already installed or in standalone mode
  const isStandalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as any).standalone ||
    document.referrer.includes('android-app://');

  // Check if PWA features are supported
  const supportsPWA = 'serviceWorker' in navigator && 'PushManager' in window;

  useEffect(() => {
    // Check if already installed
    setIsInstalled(isStandalone);

    // Listen for the beforeinstallprompt event
    const handleBeforeInstallPrompt = (e: Event) => {
      console.log('[PWA] beforeinstallprompt event fired');
      e.preventDefault();

      const promptEvent = e as BeforeInstallPromptEvent;
      setDeferredPrompt(promptEvent);
      setIsInstallable(true);

      // Show install banner after a delay (if not dismissed before)
      setTimeout(() => {
        if (!isInstalled && !localStorage.getItem('pwa-install-dismissed')) {
          setShowInstallBanner(true);
        }
      }, 10000); // Show after 10 seconds
    };

    // Listen for successful app installation
    const handleAppInstalled = () => {
      console.log('[PWA] App was installed');
      setIsInstalled(true);
      setIsInstallable(false);
      setShowInstallBanner(false);
      setDeferredPrompt(null);

      // Track installation
      if (typeof gtag !== 'undefined') {
        gtag('event', 'pwa_install', {
          event_category: 'engagement',
          event_label: 'PWA Install'
        });
      }
    };

    // Listen for PWA related events
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    // Check for iOS Safari install state
    if (navigator.userAgent.includes('iPhone') || navigator.userAgent.includes('iPad')) {
      const isIOSInstalled = localStorage.getItem('ios-pwa-installed') === 'true';
      setIsInstalled(isIOSInstalled);
    }

    // Cleanup
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, [isInstalled]);

  const installApp = async (): Promise<void> => {
    if (!deferredPrompt) {
      console.warn('[PWA] No install prompt available');
      return;
    }

    try {
      // Show the install prompt
      await deferredPrompt.prompt();

      // Wait for the user to respond to the prompt
      const choiceResult = await deferredPrompt.userChoice;

      console.log('[PWA] User choice:', choiceResult.outcome);

      if (choiceResult.outcome === 'accepted') {
        console.log('[PWA] User accepted the install prompt');
        setIsInstalled(true);
      } else {
        console.log('[PWA] User dismissed the install prompt');
        // Don't show banner again for this session
        localStorage.setItem('pwa-install-dismissed', 'true');
      }

      // Clean up
      setDeferredPrompt(null);
      setIsInstallable(false);
      setShowInstallBanner(false);
    } catch (error) {
      console.error('[PWA] Error during installation:', error);
    }
  };

  const dismissInstallPrompt = (): void => {
    setShowInstallBanner(false);
    localStorage.setItem('pwa-install-dismissed', 'true');

    // Track dismissal
    if (typeof gtag !== 'undefined') {
      gtag('event', 'pwa_install_dismissed', {
        event_category: 'engagement',
        event_label: 'PWA Install Dismissed'
      });
    }
  };

  const contextValue: PWAInstallContextType = {
    isInstallable,
    isInstalled,
    installApp,
    dismissInstallPrompt,
    showInstallBanner,
    isStandalone,
    supportsPWA,
  };

  return (
    <PWAInstallContext.Provider value={contextValue}>
      {children}
    </PWAInstallContext.Provider>
  );
};

export const usePWAInstall = (): PWAInstallContextType => {
  const context = useContext(PWAInstallContext);
  if (context === undefined) {
    throw new Error('usePWAInstall must be used within a PWAInstallProvider');
  }
  return context;
};