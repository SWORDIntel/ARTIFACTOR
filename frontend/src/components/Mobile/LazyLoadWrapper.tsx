import React, { useState, useRef, useEffect, ReactNode } from 'react';
import { Box, Skeleton, useTheme } from '@mui/material';
import { useInView } from 'react-intersection-observer';
import { motion } from 'framer-motion';

interface LazyLoadWrapperProps {
  children: ReactNode;
  height?: number | string;
  fallback?: ReactNode;
  rootMargin?: string;
  threshold?: number;
  delay?: number;
  animationType?: 'fade' | 'slide' | 'scale' | 'none';
  placeholder?: 'skeleton' | 'custom' | 'none';
}

export const LazyLoadWrapper: React.FC<LazyLoadWrapperProps> = ({
  children,
  height = 200,
  fallback,
  rootMargin = '50px',
  threshold = 0.1,
  delay = 0,
  animationType = 'fade',
  placeholder = 'skeleton',
}) => {
  const theme = useTheme();
  const [shouldLoad, setShouldLoad] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const { ref, inView } = useInView({
    threshold,
    rootMargin,
    triggerOnce: true,
  });

  useEffect(() => {
    if (inView && !shouldLoad) {
      if (delay > 0) {
        timeoutRef.current = setTimeout(() => {
          setShouldLoad(true);
        }, delay);
      } else {
        setShouldLoad(true);
      }
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [inView, shouldLoad, delay]);

  useEffect(() => {
    if (shouldLoad) {
      // Simulate loading time for demonstration
      const loadTimeout = setTimeout(() => {
        setIsLoaded(true);
      }, 100);

      return () => clearTimeout(loadTimeout);
    }
  }, [shouldLoad]);

  const getAnimationVariants = () => {
    switch (animationType) {
      case 'fade':
        return {
          hidden: { opacity: 0 },
          visible: { opacity: 1, transition: { duration: 0.5 } },
        };
      case 'slide':
        return {
          hidden: { opacity: 0, y: 20 },
          visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
        };
      case 'scale':
        return {
          hidden: { opacity: 0, scale: 0.8 },
          visible: { opacity: 1, scale: 1, transition: { duration: 0.5 } },
        };
      default:
        return {
          hidden: {},
          visible: {},
        };
    }
  };

  const renderPlaceholder = () => {
    if (fallback) {
      return fallback;
    }

    if (placeholder === 'skeleton') {
      return (
        <Box sx={{ p: 2 }}>
          <Skeleton variant="rectangular" width="100%" height={height} sx={{ borderRadius: 2 }} />
          <Box sx={{ mt: 2 }}>
            <Skeleton variant="text" width="80%" />
            <Skeleton variant="text" width="60%" />
          </Box>
        </Box>
      );
    }

    if (placeholder === 'none') {
      return (
        <Box
          sx={{
            height,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: theme.palette.grey[50],
            borderRadius: 2,
          }}
        />
      );
    }

    return null;
  };

  const variants = getAnimationVariants();

  return (
    <Box ref={ref} sx={{ minHeight: height }}>
      {!shouldLoad || !isLoaded ? (
        renderPlaceholder()
      ) : (
        <motion.div
          initial="hidden"
          animate="visible"
          variants={variants}
        >
          {children}
        </motion.div>
      )}
    </Box>
  );
};

// Hook for lazy loading images with progressive enhancement
export const useLazyImage = (src: string, placeholder?: string) => {
  const [imageSrc, setImageSrc] = useState(placeholder || '');
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    const img = new Image();

    img.onload = () => {
      setImageSrc(src);
      setIsLoading(false);
    };

    img.onerror = () => {
      setHasError(true);
      setIsLoading(false);
    };

    img.src = src;

    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [src]);

  return { imageSrc, isLoading, hasError };
};

// Component for progressive image loading
interface ProgressiveImageProps {
  src: string;
  alt: string;
  placeholder?: string;
  className?: string;
  style?: React.CSSProperties;
  onLoad?: () => void;
  onError?: () => void;
}

export const ProgressiveImage: React.FC<ProgressiveImageProps> = ({
  src,
  alt,
  placeholder,
  className,
  style,
  onLoad,
  onError,
}) => {
  const { imageSrc, isLoading, hasError } = useLazyImage(src, placeholder);

  useEffect(() => {
    if (!isLoading && !hasError && onLoad) {
      onLoad();
    }
    if (hasError && onError) {
      onError();
    }
  }, [isLoading, hasError, onLoad, onError]);

  return (
    <Box
      sx={{
        position: 'relative',
        overflow: 'hidden',
        ...style,
      }}
      className={className}
    >
      {isLoading && (
        <motion.div
          initial={{ opacity: 1 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 1,
          }}
        >
          <Skeleton
            variant="rectangular"
            width="100%"
            height="100%"
            animation="wave"
          />
        </motion.div>
      )}

      <motion.img
        src={imageSrc}
        alt={alt}
        initial={{ opacity: 0 }}
        animate={{ opacity: isLoading ? 0 : 1 }}
        transition={{ duration: 0.3 }}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          display: hasError ? 'none' : 'block',
        }}
      />

      {hasError && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'grey.100',
            color: 'text.secondary',
          }}
        >
          Failed to load image
        </Box>
      )}
    </Box>
  );
};