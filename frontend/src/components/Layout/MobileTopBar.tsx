import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Badge,
  Box,
  Chip,
  Avatar,
  useTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  Search as SearchIcon,
  Offline as OfflineIcon,
  SignalWifi4Bar as OnlineIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

interface MobileTopBarProps {
  onMenuClick: () => void;
  onAccountClick: (event: React.MouseEvent<HTMLElement>) => void;
  isOnline: boolean;
}

export const MobileTopBar: React.FC<MobileTopBarProps> = ({
  onMenuClick,
  onAccountClick,
  isOnline,
}) => {
  const theme = useTheme();

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderBottom: `1px solid ${theme.palette.divider}`,
        color: theme.palette.text.primary,
        zIndex: theme.zIndex.appBar,
      }}
    >
      <Toolbar
        sx={{
          minHeight: { xs: 56, sm: 64 },
          px: { xs: 1, sm: 2 },
        }}
      >
        {/* Menu Button */}
        <motion.div whileTap={{ scale: 0.9 }}>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={onMenuClick}
            sx={{
              mr: 1,
              p: 1.5,
            }}
          >
            <MenuIcon />
          </IconButton>
        </motion.div>

        {/* App Title */}
        <Box sx={{ flex: 1, ml: 1 }}>
          <Typography
            variant="h6"
            component="div"
            sx={{
              fontWeight: 700,
              fontSize: { xs: '1.1rem', sm: '1.25rem' },
              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            ARTIFACTOR
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: theme.palette.text.secondary,
              fontSize: '0.7rem',
              lineHeight: 1,
              display: { xs: 'block', sm: 'none' },
            }}
          >
            Mobile AI Platform
          </Typography>
        </Box>

        {/* Connection Status */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Chip
            icon={
              <motion.div
                animate={{ rotate: isOnline ? 0 : 180 }}
                transition={{ duration: 0.5 }}
              >
                {isOnline ? <OnlineIcon sx={{ fontSize: 16 }} /> : <OfflineIcon sx={{ fontSize: 16 }} />}
              </motion.div>
            }
            label={isOnline ? 'Online' : 'Offline'}
            color={isOnline ? 'success' : 'default'}
            size="small"
            variant="outlined"
            sx={{
              height: 28,
              fontSize: '0.7rem',
              mr: 1,
              '& .MuiChip-icon': {
                ml: 0.5,
              },
            }}
          />
        </motion.div>

        {/* Search Button */}
        <motion.div whileTap={{ scale: 0.9 }}>
          <IconButton
            color="inherit"
            aria-label="search"
            sx={{
              mr: 0.5,
              p: 1.5,
            }}
          >
            <SearchIcon />
          </IconButton>
        </motion.div>

        {/* Notifications */}
        <motion.div whileTap={{ scale: 0.9 }}>
          <IconButton
            color="inherit"
            aria-label="notifications"
            sx={{
              mr: 0.5,
              p: 1.5,
            }}
          >
            <Badge
              badgeContent={3}
              color="error"
              variant="dot"
              sx={{
                '& .MuiBadge-badge': {
                  top: 8,
                  right: 8,
                },
              }}
            >
              <NotificationsIcon />
            </Badge>
          </IconButton>
        </motion.div>

        {/* Account Menu */}
        <motion.div whileTap={{ scale: 0.9 }}>
          <IconButton
            color="inherit"
            onClick={onAccountClick}
            sx={{
              p: 0.5,
            }}
          >
            <Avatar
              sx={{
                width: 36,
                height: 36,
                backgroundColor: theme.palette.primary.main,
                fontSize: '1rem',
                fontWeight: 600,
              }}
            >
              U
            </Avatar>
          </IconButton>
        </motion.div>
      </Toolbar>

      {/* Progress indicator for loading states */}
      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 1,
          backgroundColor: theme.palette.primary.main,
          transformOrigin: 'left',
        }}
      />
    </AppBar>
  );
};