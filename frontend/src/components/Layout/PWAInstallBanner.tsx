import React from 'react';
import {
  Paper,
  Typography,
  Button,
  IconButton,
  Box,
  Chip,
  useTheme,
} from '@mui/material';
import {
  InstallMobile as InstallIcon,
  Close as CloseIcon,
  Smartphone as PhoneIcon,
  Offline as OfflineIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

interface PWAInstallBannerProps {
  onInstall: () => void;
  onDismiss: () => void;
}

export const PWAInstallBanner: React.FC<PWAInstallBannerProps> = ({
  onInstall,
  onDismiss,
}) => {
  const theme = useTheme();

  return (
    <Paper
      elevation={4}
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 1300,
        background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
        color: 'white',
        overflow: 'hidden',
      }}
    >
      <motion.div
        initial={{ backgroundPosition: '0% 50%' }}
        animate={{ backgroundPosition: '100% 50%' }}
        transition={{ duration: 10, repeat: Infinity, repeatType: 'reverse' }}
        style={{
          background: 'linear-gradient(45deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))',
          backgroundSize: '200% 200%',
          padding: theme.spacing(2),
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* App Icon */}
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2,
              background: 'rgba(255, 255, 255, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backdropFilter: 'blur(10px)',
            }}
          >
            <InstallIcon sx={{ fontSize: 28 }} />
          </Box>

          {/* Content */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
              Install ARTIFACTOR
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
              Get the full app experience with offline access and native performance
            </Typography>

            {/* Feature Chips */}
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                icon={<OfflineIcon sx={{ fontSize: 16 }} />}
                label="Offline Access"
                size="small"
                sx={{
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  '& .MuiChip-icon': { color: 'white' },
                }}
              />
              <Chip
                icon={<SpeedIcon sx={{ fontSize: 16 }} />}
                label="Fast Loading"
                size="small"
                sx={{
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  '& .MuiChip-icon': { color: 'white' },
                }}
              />
              <Chip
                icon={<PhoneIcon sx={{ fontSize: 16 }} />}
                label="Native Feel"
                size="small"
                sx={{
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  '& .MuiChip-icon': { color: 'white' },
                }}
              />
            </Box>
          </Box>

          {/* Actions */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Button
              variant="contained"
              onClick={onInstall}
              sx={{
                backgroundColor: 'white',
                color: theme.palette.primary.main,
                fontWeight: 600,
                minWidth: 100,
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.9)',
                },
              }}
              startIcon={<InstallIcon />}
            >
              Install
            </Button>

            <IconButton
              onClick={onDismiss}
              size="small"
              sx={{
                color: 'rgba(255, 255, 255, 0.7)',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>

        {/* Progress indicator */}
        <motion.div
          initial={{ width: '0%' }}
          animate={{ width: '100%' }}
          transition={{ duration: 15, ease: 'linear' }}
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            height: 2,
            backgroundColor: 'rgba(255, 255, 255, 0.3)',
          }}
        />
      </motion.div>
    </Paper>
  );
};