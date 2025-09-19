import React from 'react';
import {
  Paper,
  BottomNavigation as MuiBottomNavigation,
  BottomNavigationAction,
  Badge,
  Box,
  useTheme,
} from '@mui/material';
import { motion } from 'framer-motion';

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  badge?: number;
}

interface BottomNavigationProps {
  navigationItems: NavigationItem[];
  currentPath: string;
  onNavigate: (path: string) => void;
}

export const BottomNavigation: React.FC<BottomNavigationProps> = ({
  navigationItems,
  currentPath,
  onNavigate,
}) => {
  const theme = useTheme();

  // Get current navigation index
  const currentIndex = navigationItems.findIndex(item => item.path === currentPath);

  return (
    <Paper
      elevation={8}
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        borderTop: `1px solid ${theme.palette.divider}`,
        backgroundColor: theme.palette.background.paper,
        backdropFilter: 'blur(20px)',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          zIndex: -1,
        },
      }}
    >
      {/* Active indicator */}
      {currentIndex >= 0 && (
        <motion.div
          layoutId="activeTab"
          style={{
            position: 'absolute',
            top: 0,
            height: 3,
            backgroundColor: theme.palette.primary.main,
            borderRadius: '0 0 2px 2px',
          }}
          initial={false}
          animate={{
            left: `${(currentIndex * 100) / navigationItems.length}%`,
            width: `${100 / navigationItems.length}%`,
          }}
          transition={{
            type: 'spring',
            stiffness: 300,
            damping: 30,
          }}
        />
      )}

      <MuiBottomNavigation
        value={currentIndex}
        onChange={(event, newValue) => {
          if (newValue >= 0 && newValue < navigationItems.length) {
            onNavigate(navigationItems[newValue].path);
          }
        }}
        sx={{
          backgroundColor: 'transparent',
          '& .MuiBottomNavigationAction-root': {
            minWidth: 'auto',
            paddingTop: theme.spacing(1),
            paddingBottom: theme.spacing(1),
            '&.Mui-selected': {
              color: theme.palette.primary.main,
              '& .MuiBottomNavigationAction-label': {
                fontSize: '0.75rem',
                fontWeight: 600,
              },
            },
            '&:not(.Mui-selected)': {
              color: theme.palette.text.secondary,
            },
          },
          '& .MuiBottomNavigationAction-label': {
            fontSize: '0.7rem',
            fontWeight: 500,
            opacity: 1,
            '&.Mui-selected': {
              fontSize: '0.75rem',
            },
          },
        }}
      >
        {navigationItems.map((item, index) => (
          <BottomNavigationAction
            key={item.id}
            label={item.label}
            icon={
              item.badge ? (
                <Badge badgeContent={item.badge} color="error" variant="dot">
                  <motion.div
                    whileTap={{ scale: 0.9 }}
                    whileHover={{ scale: 1.1 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 17 }}
                  >
                    {item.icon}
                  </motion.div>
                </Badge>
              ) : (
                <motion.div
                  whileTap={{ scale: 0.9 }}
                  whileHover={{ scale: 1.1 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 17 }}
                >
                  {item.icon}
                </motion.div>
              )
            }
            sx={{
              position: 'relative',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: '50%',
                left: '50%',
                width: 0,
                height: 0,
                borderRadius: '50%',
                backgroundColor: theme.palette.primary.main,
                opacity: 0,
                transform: 'translate(-50%, -50%)',
                transition: 'all 0.2s ease-in-out',
              },
              '&.Mui-selected::before': {
                width: 40,
                height: 40,
                opacity: 0.1,
              },
            }}
          />
        ))}
      </MuiBottomNavigation>

      {/* Safe area spacer for devices with home indicator */}
      <Box
        sx={{
          height: 'env(safe-area-inset-bottom, 0px)',
          backgroundColor: 'inherit',
        }}
      />
    </Paper>
  );
};