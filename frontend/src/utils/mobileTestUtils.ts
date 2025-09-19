// Mobile Enhancement Testing Utilities for ARTIFACTOR v3.0

export interface MobileTestResults {
  pwa: {
    manifestValid: boolean;
    serviceWorkerRegistered: boolean;
    installable: boolean;
    offline: boolean;
  };
  responsive: {
    touchTargets: boolean;
    viewport: boolean;
    typography: boolean;
    navigation: boolean;
  };
  performance: {
    lazyLoading: boolean;
    imageOptimization: boolean;
    caching: boolean;
    backgroundSync: boolean;
  };
  gestures: {
    swipe: boolean;
    pinch: boolean;
    longPress: boolean;
    doubleTap: boolean;
  };
  collaboration: {
    realTime: boolean;
    offline: boolean;
    mobileOptimized: boolean;
  };
}

export class MobileTestSuite {
  private results: Partial<MobileTestResults> = {};

  async runAllTests(): Promise<MobileTestResults> {
    console.log('🧪 Starting ARTIFACTOR v3.0 Mobile Enhancement Tests...');

    await this.testPWAFeatures();
    await this.testResponsiveDesign();
    await this.testPerformanceOptimizations();
    await this.testTouchGestures();
    await this.testCollaborationFeatures();

    console.log('✅ Mobile Enhancement Tests Complete!');
    return this.results as MobileTestResults;
  }

  private async testPWAFeatures(): Promise<void> {
    console.log('📱 Testing PWA Features...');

    const pwaResults = {
      manifestValid: await this.checkManifest(),
      serviceWorkerRegistered: await this.checkServiceWorker(),
      installable: await this.checkInstallability(),
      offline: await this.checkOfflineCapability(),
    };

    this.results.pwa = pwaResults;
    console.log('PWA Results:', pwaResults);
  }

  private async testResponsiveDesign(): Promise<void> {
    console.log('📐 Testing Responsive Design...');

    const responsiveResults = {
      touchTargets: this.checkTouchTargets(),
      viewport: this.checkViewportMeta(),
      typography: this.checkResponsiveTypography(),
      navigation: this.checkMobileNavigation(),
    };

    this.results.responsive = responsiveResults;
    console.log('Responsive Results:', responsiveResults);
  }

  private async testPerformanceOptimizations(): Promise<void> {
    console.log('⚡ Testing Performance Optimizations...');

    const performanceResults = {
      lazyLoading: this.checkLazyLoading(),
      imageOptimization: this.checkImageOptimization(),
      caching: await this.checkCaching(),
      backgroundSync: await this.checkBackgroundSync(),
    };

    this.results.performance = performanceResults;
    console.log('Performance Results:', performanceResults);
  }

  private async testTouchGestures(): Promise<void> {
    console.log('👆 Testing Touch Gestures...');

    const gestureResults = {
      swipe: this.checkSwipeGestures(),
      pinch: this.checkPinchGestures(),
      longPress: this.checkLongPressGestures(),
      doubleTap: this.checkDoubleTapGestures(),
    };

    this.results.gestures = gestureResults;
    console.log('Gesture Results:', gestureResults);
  }

  private async testCollaborationFeatures(): Promise<void> {
    console.log('🤝 Testing Collaboration Features...');

    const collaborationResults = {
      realTime: await this.checkRealTimeCollaboration(),
      offline: await this.checkOfflineCollaboration(),
      mobileOptimized: this.checkMobileCollaborationUI(),
    };

    this.results.collaboration = collaborationResults;
    console.log('Collaboration Results:', collaborationResults);
  }

  // PWA Test Methods
  private async checkManifest(): Promise<boolean> {
    try {
      const response = await fetch('/manifest.json');
      const manifest = await response.json();

      const requiredFields = ['name', 'short_name', 'start_url', 'display', 'icons'];
      return requiredFields.every(field => manifest[field]);
    } catch (error) {
      console.error('Manifest check failed:', error);
      return false;
    }
  }

  private async checkServiceWorker(): Promise<boolean> {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.getRegistration();
        return !!registration;
      } catch (error) {
        console.error('Service Worker check failed:', error);
        return false;
      }
    }
    return false;
  }

  private async checkInstallability(): Promise<boolean> {
    // Check if beforeinstallprompt event can be triggered
    return new Promise((resolve) => {
      let hasPrompt = false;

      const handler = () => {
        hasPrompt = true;
        resolve(true);
      };

      window.addEventListener('beforeinstallprompt', handler);

      setTimeout(() => {
        window.removeEventListener('beforeinstallprompt', handler);
        resolve(hasPrompt);
      }, 1000);
    });
  }

  private async checkOfflineCapability(): Promise<boolean> {
    try {
      // Test cache functionality
      const cache = await caches.open('artifactor-test');
      await cache.add('/');
      return true;
    } catch (error) {
      console.error('Offline capability check failed:', error);
      return false;
    }
  }

  // Responsive Design Test Methods
  private checkTouchTargets(): boolean {
    const buttons = document.querySelectorAll('button, [role="button"]');
    const validTargets = Array.from(buttons).filter(button => {
      const rect = button.getBoundingClientRect();
      return rect.width >= 44 && rect.height >= 44; // 44px minimum for touch targets
    });

    return validTargets.length / buttons.length > 0.8; // 80% of buttons should be touch-friendly
  }

  private checkViewportMeta(): boolean {
    const viewportMeta = document.querySelector('meta[name="viewport"]');
    if (!viewportMeta) return false;

    const content = viewportMeta.getAttribute('content') || '';
    return content.includes('width=device-width') && content.includes('initial-scale=1');
  }

  private checkResponsiveTypography(): boolean {
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let responsiveCount = 0;

    headings.forEach(heading => {
      const styles = window.getComputedStyle(heading);
      const fontSize = styles.fontSize;

      // Check if using responsive units (rem, em, clamp, etc.)
      if (fontSize.includes('clamp') || fontSize.includes('rem') || fontSize.includes('em')) {
        responsiveCount++;
      }
    });

    return responsiveCount / headings.length > 0.7; // 70% should use responsive typography
  }

  private checkMobileNavigation(): boolean {
    // Check for mobile-specific navigation elements
    const mobileNav = document.querySelector('[data-testid="mobile-navigation"]') ||
                     document.querySelector('.mobile-nav') ||
                     document.querySelector('nav[aria-label*="mobile"]');

    const bottomNav = document.querySelector('[data-testid="bottom-navigation"]') ||
                     document.querySelector('.bottom-navigation');

    return !!(mobileNav || bottomNav);
  }

  // Performance Test Methods
  private checkLazyLoading(): boolean {
    const images = document.querySelectorAll('img');
    const lazyImages = Array.from(images).filter(img =>
      img.loading === 'lazy' ||
      img.hasAttribute('data-src') ||
      img.classList.contains('lazy')
    );

    return lazyImages.length > 0;
  }

  private checkImageOptimization(): boolean {
    const images = document.querySelectorAll('img');
    let optimizedCount = 0;

    images.forEach(img => {
      // Check for modern image formats or responsive images
      if (img.srcset ||
          img.src.includes('webp') ||
          img.src.includes('avif') ||
          img.parentElement?.tagName === 'PICTURE') {
        optimizedCount++;
      }
    });

    return optimizedCount / images.length > 0.5; // 50% should be optimized
  }

  private async checkCaching(): Promise<boolean> {
    try {
      const cacheNames = await caches.keys();
      return cacheNames.some(name => name.includes('artifactor'));
    } catch (error) {
      console.error('Cache check failed:', error);
      return false;
    }
  }

  private async checkBackgroundSync(): Promise<boolean> {
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      try {
        const registration = await navigator.serviceWorker.ready;
        // Test sync registration (this doesn't actually sync, just checks capability)
        await registration.sync.register('test-sync');
        return true;
      } catch (error) {
        console.error('Background sync check failed:', error);
        return false;
      }
    }
    return false;
  }

  // Touch Gesture Test Methods
  private checkSwipeGestures(): boolean {
    // Check if swipe gesture handlers are attached
    const swipeElements = document.querySelectorAll('[data-swipe]') ||
                         document.querySelectorAll('.swipeable');
    return swipeElements.length > 0;
  }

  private checkPinchGestures(): boolean {
    // Check for pinch/zoom gesture support
    const pinchElements = document.querySelectorAll('[data-pinch]') ||
                         document.querySelectorAll('.pinchable');
    return pinchElements.length > 0;
  }

  private checkLongPressGestures(): boolean {
    // Check for long press gesture handlers
    const longPressElements = document.querySelectorAll('[data-long-press]') ||
                             document.querySelectorAll('.long-pressable');
    return longPressElements.length > 0;
  }

  private checkDoubleTapGestures(): boolean {
    // Check for double tap gesture handlers
    const doubleTapElements = document.querySelectorAll('[data-double-tap]') ||
                             document.querySelectorAll('.double-tappable');
    return doubleTapElements.length > 0;
  }

  // Collaboration Test Methods
  private async checkRealTimeCollaboration(): Promise<boolean> {
    // Check for WebSocket connection or real-time features
    return new Promise((resolve) => {
      if (window.WebSocket) {
        // Look for active WebSocket connections or collaboration features
        const collaborationElements = document.querySelectorAll('[data-collaboration]') ||
                                    document.querySelectorAll('.collaboration');
        resolve(collaborationElements.length > 0);
      } else {
        resolve(false);
      }
    });
  }

  private async checkOfflineCollaboration(): Promise<boolean> {
    // Check for offline collaboration capabilities
    try {
      const db = await this.openIndexedDB();
      const stores = db.objectStoreNames;
      return Array.from(stores).some(store => store.includes('collaboration'));
    } catch (error) {
      console.error('Offline collaboration check failed:', error);
      return false;
    }
  }

  private checkMobileCollaborationUI(): boolean {
    // Check for mobile-optimized collaboration UI
    const mobileCollabElements = document.querySelectorAll('[data-mobile-collaboration]') ||
                               document.querySelectorAll('.mobile-collaboration');
    return mobileCollabElements.length > 0;
  }

  private openIndexedDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('artifactor-offline', 1);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  // Utility method to generate test report
  generateReport(): string {
    const results = this.results as MobileTestResults;
    const scores = {
      pwa: this.calculateScore(results.pwa),
      responsive: this.calculateScore(results.responsive),
      performance: this.calculateScore(results.performance),
      gestures: this.calculateScore(results.gestures),
      collaboration: this.calculateScore(results.collaboration),
    };

    const overallScore = Object.values(scores).reduce((a, b) => a + b, 0) / Object.keys(scores).length;

    return `
# ARTIFACTOR v3.0 Mobile Enhancement Test Report

## Overall Score: ${Math.round(overallScore * 100)}%

### PWA Features: ${Math.round(scores.pwa * 100)}%
- Manifest Valid: ${results.pwa?.manifestValid ? '✅' : '❌'}
- Service Worker: ${results.pwa?.serviceWorkerRegistered ? '✅' : '❌'}
- Installable: ${results.pwa?.installable ? '✅' : '❌'}
- Offline Support: ${results.pwa?.offline ? '✅' : '❌'}

### Responsive Design: ${Math.round(scores.responsive * 100)}%
- Touch Targets: ${results.responsive?.touchTargets ? '✅' : '❌'}
- Viewport Meta: ${results.responsive?.viewport ? '✅' : '❌'}
- Typography: ${results.responsive?.typography ? '✅' : '❌'}
- Mobile Navigation: ${results.responsive?.navigation ? '✅' : '❌'}

### Performance: ${Math.round(scores.performance * 100)}%
- Lazy Loading: ${results.performance?.lazyLoading ? '✅' : '❌'}
- Image Optimization: ${results.performance?.imageOptimization ? '✅' : '❌'}
- Caching: ${results.performance?.caching ? '✅' : '❌'}
- Background Sync: ${results.performance?.backgroundSync ? '✅' : '❌'}

### Touch Gestures: ${Math.round(scores.gestures * 100)}%
- Swipe Gestures: ${results.gestures?.swipe ? '✅' : '❌'}
- Pinch Gestures: ${results.gestures?.pinch ? '✅' : '❌'}
- Long Press: ${results.gestures?.longPress ? '✅' : '❌'}
- Double Tap: ${results.gestures?.doubleTap ? '✅' : '❌'}

### Collaboration: ${Math.round(scores.collaboration * 100)}%
- Real-time: ${results.collaboration?.realTime ? '✅' : '❌'}
- Offline Support: ${results.collaboration?.offline ? '✅' : '❌'}
- Mobile Optimized: ${results.collaboration?.mobileOptimized ? '✅' : '❌'}

## Recommendations:
${this.generateRecommendations(scores)}
    `;
  }

  private calculateScore(section: any): number {
    if (!section) return 0;
    const values = Object.values(section) as boolean[];
    return values.filter(v => v).length / values.length;
  }

  private generateRecommendations(scores: any): string {
    const recommendations: string[] = [];

    if (scores.pwa < 0.8) {
      recommendations.push('- Improve PWA implementation: ensure manifest is complete and service worker is properly configured');
    }
    if (scores.responsive < 0.8) {
      recommendations.push('- Enhance responsive design: ensure all touch targets meet minimum size requirements');
    }
    if (scores.performance < 0.8) {
      recommendations.push('- Optimize performance: implement lazy loading and improve caching strategies');
    }
    if (scores.gestures < 0.8) {
      recommendations.push('- Add more touch gesture support for better mobile user experience');
    }
    if (scores.collaboration < 0.8) {
      recommendations.push('- Improve mobile collaboration features and offline synchronization');
    }

    return recommendations.length > 0 ? recommendations.join('\n') : '- All mobile enhancements are performing well!';
  }
}

// Export for easy testing
export const runMobileTests = async (): Promise<string> => {
  const testSuite = new MobileTestSuite();
  await testSuite.runAllTests();
  return testSuite.generateReport();
};