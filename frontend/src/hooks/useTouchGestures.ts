import { useGesture } from 'react-use-gesture';
import { useCallback, useRef } from 'react';

interface TouchGestureConfig {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  onPinch?: (scale: number) => void;
  onTap?: () => void;
  onLongPress?: () => void;
  onDoubleTap?: () => void;
  threshold?: number;
  pinchThreshold?: number;
  longPressDelay?: number;
}

export const useTouchGestures = (config: TouchGestureConfig) => {
  const {
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    onPinch,
    onTap,
    onLongPress,
    onDoubleTap,
    threshold = 50,
    pinchThreshold = 0.1,
    longPressDelay = 500,
  } = config;

  const lastTap = useRef<number>(0);
  const longPressTimer = useRef<NodeJS.Timeout | null>(null);

  const clearLongPressTimer = useCallback(() => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  }, []);

  const bind = useGesture(
    {
      onDrag: ({ movement: [mx, my], direction: [xDir, yDir], distance, cancel }) => {
        if (distance > threshold) {
          clearLongPressTimer();

          if (Math.abs(mx) > Math.abs(my)) {
            // Horizontal swipe
            if (xDir > 0 && onSwipeRight) {
              onSwipeRight();
              cancel();
            } else if (xDir < 0 && onSwipeLeft) {
              onSwipeLeft();
              cancel();
            }
          } else {
            // Vertical swipe
            if (yDir > 0 && onSwipeDown) {
              onSwipeDown();
              cancel();
            } else if (yDir < 0 && onSwipeUp) {
              onSwipeUp();
              cancel();
            }
          }
        }
      },

      onPinch: ({ offset: [scale], cancel }) => {
        if (onPinch && Math.abs(scale - 1) > pinchThreshold) {
          onPinch(scale);
          cancel();
        }
      },

      onPointerDown: () => {
        // Start long press timer
        if (onLongPress) {
          longPressTimer.current = setTimeout(() => {
            onLongPress();
            longPressTimer.current = null;
          }, longPressDelay);
        }
      },

      onPointerUp: ({ tap }) => {
        clearLongPressTimer();

        if (tap && (onTap || onDoubleTap)) {
          const now = Date.now();
          const timeDiff = now - lastTap.current;

          if (timeDiff < 300 && onDoubleTap) {
            // Double tap detected
            onDoubleTap();
            lastTap.current = 0; // Reset to prevent triple tap issues
          } else if (onTap) {
            // Single tap
            setTimeout(() => {
              if (Date.now() - lastTap.current > 250) {
                onTap();
              }
            }, 250);
          }

          lastTap.current = now;
        }
      },

      onPointerCancel: () => {
        clearLongPressTimer();
      },
    },
    {
      drag: {
        threshold: 10,
        pointer: { touch: true },
      },
      pinch: {
        pointer: { touch: true },
      },
    }
  );

  return bind;
};

// Hook for pull-to-refresh functionality
export const usePullToRefresh = (onRefresh: () => Promise<void> | void) => {
  const isRefreshing = useRef(false);

  const bind = useGesture({
    onDrag: async ({ movement: [, my], direction: [, yDir], cancel }) => {
      // Only trigger on downward pull at the top of the page
      if (window.scrollY === 0 && yDir > 0 && my > 100 && !isRefreshing.current) {
        isRefreshing.current = true;
        cancel();

        try {
          await onRefresh();
        } finally {
          isRefreshing.current = false;
        }
      }
    },
  });

  return bind;
};

// Hook for infinite scroll
export const useInfiniteScroll = (
  onLoadMore: () => Promise<void> | void,
  hasMore: boolean = true,
  threshold: number = 100
) => {
  const isLoading = useRef(false);

  const bind = useGesture({
    onScroll: async ({ xy: [, y] }) => {
      const element = document.documentElement;
      const scrollHeight = element.scrollHeight;
      const clientHeight = element.clientHeight;

      if (
        hasMore &&
        !isLoading.current &&
        scrollHeight - (y + clientHeight) < threshold
      ) {
        isLoading.current = true;

        try {
          await onLoadMore();
        } finally {
          isLoading.current = false;
        }
      }
    },
  });

  return bind;
};

// Hook for swipe-to-dismiss functionality
export const useSwipeToDismiss = (
  onDismiss: () => void,
  threshold: number = 150
) => {
  const bind = useGesture({
    onDrag: ({ movement: [mx], direction: [xDir], cancel }) => {
      if (Math.abs(mx) > threshold) {
        onDismiss();
        cancel();
      }
    },
  });

  return bind;
};