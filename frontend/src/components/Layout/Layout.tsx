import React, { useState, useEffect } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  useTheme,
  useMediaQuery,
  Fab,
  Badge,
  Avatar,
  Menu,
  MenuItem,
  Chip,
  Slide,
  Paper,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  CloudUpload as UploadIcon,
  Folder as ArtifactsIcon,
  SmartToy as AgentsIcon,
  Settings as SettingsIcon,
  Add as AddIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountIcon,
  Close as CloseIcon,
  InstallMobile as InstallIcon,
  Offline as OfflineIcon,
  SignalWifi4Bar as OnlineIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useGesture } from 'react-use-gesture';
import { usePWAInstall } from '../../hooks/usePWAInstall';
import { PWAInstallBanner } from './PWAInstallBanner';
import { BottomNavigation } from './BottomNavigation';
import { MobileTopBar } from './MobileTopBar';

interface LayoutProps {
  children: React.ReactNode;
}

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  badge?: number;
}

const navigationItems: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <DashboardIcon />,
    path: '/dashboard',
  },
  {
    id: 'artifacts',
    label: 'Artifacts',
    icon: <ArtifactsIcon />,
    path: '/artifacts',
  },
  {
    id: 'upload',
    label: 'Upload',
    icon: <UploadIcon />,
    path: '/upload',
  },
  {
    id: 'agents',
    label: 'Agents',
    icon: <AgentsIcon />,
    path: '/agents',
    badge: 3, // Example: 3 active agents
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: <SettingsIcon />,
    path: '/settings',
  },
];

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [accountMenuAnchor, setAccountMenuAnchor] = useState<null | HTMLElement>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showScrollTop, setShowScrollTop] = useState(false);

  const { showInstallBanner, isInstalled, installApp, dismissInstallPrompt } = usePWAInstall();

  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Handle scroll to show/hide scroll-to-top button
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.pageYOffset > 300);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Swipe gesture handling for mobile drawer
  const bind = useGesture({
    onDrag: ({ movement: [mx], direction: [xDir], distance, cancel }) => {
      if (isMobile && Math.abs(mx) > 50) {
        if (xDir > 0 && mx > 100 && !mobileDrawerOpen) {
          setMobileDrawerOpen(true);
          cancel();
        } else if (xDir < 0 && mx < -100 && mobileDrawerOpen) {
          setMobileDrawerOpen(false);
          cancel();
        }
      }
    },
  });

  const handleNavigate = (path: string) => {
    navigate(path);
    if (isMobile) {
      setMobileDrawerOpen(false);
    }
  };

  const handleAccountMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAccountMenuAnchor(event.currentTarget);
  };

  const handleAccountMenuClose = () => {
    setAccountMenuAnchor(null);
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const drawerContent = (
    <Box sx={{ width: 280, pt: 2 }}>
      {/* App Logo/Title */}
      <Box sx={{ px: 2, pb: 2 }}>
        <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          ARTIFACTOR v3.0
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Mobile-Ready AI Platform
        </Typography>
      </Box>

      <Divider />

      {/* Navigation Items */}
      <List sx={{ px: 1, pt: 1 }}>
        {navigationItems.map((item) => (
          <ListItem key={item.id} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              onClick={() => handleNavigate(item.path)}
              selected={location.pathname === item.path}
              sx={{
                borderRadius: 2,
                mx: 1,
                '&.Mui-selected': {
                  backgroundColor: 'primary.main',
                  color: 'white',
                  '& .MuiListItemIcon-root': {
                    color: 'white',
                  },
                },
                '&:hover': {
                  backgroundColor: location.pathname === item.path ? 'primary.dark' : 'action.hover',
                },
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: 40,
                  color: location.pathname === item.path ? 'inherit' : 'action.active',
                }}
              >
                {item.badge ? (
                  <Badge badgeContent={item.badge} color="error">
                    {item.icon}
                  </Badge>
                ) : (
                  item.icon
                )}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{
                  fontSize: '0.9rem',
                  fontWeight: location.pathname === item.path ? 600 : 400,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider sx={{ mt: 2, mb: 2 }} />

      {/* Connection Status */}
      <Box sx={{ px: 2, pb: 2 }}>
        <Chip
          icon={isOnline ? <OnlineIcon /> : <OfflineIcon />}
          label={isOnline ? 'Online' : 'Offline'}
          color={isOnline ? 'success' : 'default'}
          size="small"
          variant="outlined"
        />
        {!isInstalled && (
          <Chip
            icon={<InstallIcon />}
            label="Install App"
            color="primary"
            size="small"
            variant="outlined"
            onClick={installApp}
            sx={{ ml: 1 }}
          />
        )}
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }} {...bind()}>
      {/* PWA Install Banner */}
      <AnimatePresence>
        {showInstallBanner && (
          <motion.div
            initial={{ y: -100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -100, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <PWAInstallBanner onInstall={installApp} onDismiss={dismissInstallPrompt} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile Top Bar */}
      {isMobile ? (
        <MobileTopBar
          onMenuClick={() => setMobileDrawerOpen(true)}
          onAccountClick={handleAccountMenuOpen}
          isOnline={isOnline}
        />
      ) : (
        /* Desktop App Bar */
        <AppBar position="fixed" elevation={1}>
          <Toolbar>
            <IconButton
              edge="start"
              color="inherit"
              aria-label="menu"
              onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
              sx={{ mr: 2, display: { md: 'none' } }}
            >
              <MenuIcon />
            </IconButton>

            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              ARTIFACTOR v3.0
            </Typography>

            {/* Connection Status */}
            <Chip
              icon={isOnline ? <OnlineIcon /> : <OfflineIcon />}
              label={isOnline ? 'Online' : 'Offline'}
              color={isOnline ? 'success' : 'default'}
              size="small"
              variant="outlined"
              sx={{ mr: 2 }}
            />

            {/* Notifications */}
            <IconButton color="inherit" sx={{ mr: 1 }}>
              <Badge badgeContent={3} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>

            {/* Account Menu */}
            <IconButton color="inherit" onClick={handleAccountMenuOpen}>
              <Avatar sx={{ width: 32, height: 32 }}>U</Avatar>
            </IconButton>
          </Toolbar>
        </AppBar>
      )}

      {/* Mobile Drawer */}
      <Drawer
        anchor="left"
        open={mobileDrawerOpen}
        onClose={() => setMobileDrawerOpen(false)}
        ModalProps={{
          keepMounted: true, // Better mobile performance
        }}
        sx={{
          display: { xs: 'block', md: isMobile ? 'block' : 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: 280,
          },
        }}
      >
        {/* Close button for mobile */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 1 }}>
          <IconButton onClick={() => setMobileDrawerOpen(false)}>
            <CloseIcon />
          </IconButton>
        </Box>
        {drawerContent}
      </Drawer>

      {/* Desktop Persistent Drawer */}
      {!isMobile && (
        <Drawer
          variant="persistent"
          anchor="left"
          open={!isMobile}
          sx={{
            width: 280,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: 280,
              boxSizing: 'border-box',
              top: 64, // Below app bar
              height: 'calc(100% - 64px)',
            },
          }}
        >
          {drawerContent}
        </Drawer>
      )}

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          mt: isMobile ? 7 : 8, // Account for mobile top bar height
          ml: !isMobile ? '280px' : 0,
          mb: isMobile ? 7 : 0, // Account for bottom navigation
          px: isMobile ? 1 : 3,
          py: isMobile ? 1 : 2,
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {children}
        </motion.div>
      </Box>

      {/* Mobile Bottom Navigation */}
      {isMobile && (
        <BottomNavigation
          navigationItems={navigationItems}
          currentPath={location.pathname}
          onNavigate={handleNavigate}
        />
      )}

      {/* Floating Action Button for Quick Upload */}
      {!location.pathname.includes('/upload') && (
        <Fab
          color="primary"
          aria-label="upload"
          onClick={() => handleNavigate('/upload')}
          sx={{
            position: 'fixed',
            bottom: isMobile ? 80 : 24,
            right: 24,
            zIndex: 1000,
          }}
        >
          <AddIcon />
        </Fab>
      )}

      {/* Scroll to Top Button */}
      <Slide direction="up" in={showScrollTop} mountOnEnter unmountOnExit>
        <Fab
          size="small"
          color="secondary"
          aria-label="scroll to top"
          onClick={scrollToTop}
          sx={{
            position: 'fixed',
            bottom: isMobile ? 140 : 84,
            right: 24,
            zIndex: 999,
          }}
        >
          <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
            ↑
          </Typography>
        </Fab>
      </Slide>

      {/* Account Menu */}
      <Menu
        anchorEl={accountMenuAnchor}
        open={Boolean(accountMenuAnchor)}
        onClose={handleAccountMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={handleAccountMenuClose}>Profile</MenuItem>
        <MenuItem onClick={handleAccountMenuClose}>My Account</MenuItem>
        <MenuItem onClick={handleAccountMenuClose}>Logout</MenuItem>
      </Menu>
    </Box>
  );
};

export default Layout;