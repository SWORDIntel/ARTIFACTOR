import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { PWAInstallProvider } from './contexts/PWAInstallContext';
import { usePWAInstall } from './hooks/usePWAInstall';

// Contexts
import { AuthProvider } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';

// Components
import Layout from './components/Layout/Layout';
import ProtectedRoute from './components/Auth/ProtectedRoute';

// Pages
import LoginPage from './pages/Auth/LoginPage';
import RegisterPage from './pages/Auth/RegisterPage';
import DashboardPage from './pages/Dashboard/DashboardPage';
import ArtifactsPage from './pages/Artifacts/ArtifactsPage';
import ArtifactDetailPage from './pages/Artifacts/ArtifactDetailPage';
import UploadPage from './pages/Upload/UploadPage';
import SettingsPage from './pages/Settings/SettingsPage';
import AgentMonitorPage from './pages/Agents/AgentMonitorPage';

// Create mobile-responsive Material-UI theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
      light: '#ff5983',
      dark: '#9a0036',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
      fontWeight: 500,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: 'clamp(1.5rem, 3.5vw, 2rem)',
      fontWeight: 500,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: 'clamp(1.25rem, 3vw, 1.75rem)',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    body1: {
      fontSize: 'clamp(0.875rem, 2.5vw, 1rem)',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: 'clamp(0.75rem, 2vw, 0.875rem)',
      lineHeight: 1.5,
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      xl: 1536,
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        '*': {
          boxSizing: 'border-box',
        },
        html: {
          WebkitFontSmoothing: 'antialiased',
          MozOsxFontSmoothing: 'grayscale',
          height: '100%',
          width: '100%',
          overflow: 'hidden',
        },
        body: {
          height: '100%',
          width: '100%',
          margin: 0,
          padding: 0,
          overflowX: 'hidden',
          touchAction: 'manipulation', // Prevent double-tap zoom
        },
        '#root': {
          height: '100%',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
          minHeight: 44, // Touch-friendly size
          padding: '12px 24px',
          '@media (max-width: 600px)': {
            minHeight: 48, // Larger on mobile
            padding: '14px 20px',
            fontSize: '1rem',
          },
        },
        contained: {
          boxShadow: '0 2px 8px rgba(25, 118, 210, 0.24)',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(25, 118, 210, 0.32)',
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          padding: 12,
          '@media (max-width: 600px)': {
            padding: 16, // Larger touch targets on mobile
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          '@media (max-width: 600px)': {
            borderRadius: 8,
            margin: '8px',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: '#333333',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          zIndex: 1201, // Above drawer
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          '@media (max-width: 600px)': {
            width: '80%',
            maxWidth: 320,
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiInputBase-root': {
            minHeight: 44,
            '@media (max-width: 600px)': {
              minHeight: 48,
              fontSize: '16px', // Prevent zoom on iOS
            },
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          '@media (max-width: 600px)': {
            padding: '8px 4px',
            fontSize: '0.75rem',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          '@media (max-width: 600px)': {
            height: 28,
            fontSize: '0.75rem',
          },
        },
      },
    },
    MuiFab: {
      styleOverrides: {
        root: {
          '@media (max-width: 600px)': {
            width: 56,
            height: 56,
            bottom: 16,
            right: 16,
            position: 'fixed',
          },
        },
      },
    },
  },
});

const App: React.FC = () => {
  // Register service worker for PWA functionality
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', async () => {
        try {
          const registration = await navigator.serviceWorker.register('/sw.js');
          console.log('SW registered successfully:', registration);

          // Listen for updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  // New content available
                  console.log('New content available, please refresh.');

                  // You could show a notification here
                  if (window.confirm('New version available! Refresh to update?')) {
                    window.location.reload();
                  }
                }
              });
            }
          });
        } catch (error) {
          console.error('SW registration failed:', error);
        }
      });
    }

    // Handle mobile-specific viewport adjustments
    const handleViewportChange = () => {
      // Adjust viewport height for mobile browsers with dynamic UI
      if (window.visualViewport) {
        const viewport = window.visualViewport;
        const handleResize = () => {
          document.documentElement.style.setProperty(
            '--viewport-height',
            `${viewport.height}px`
          );
        };

        viewport.addEventListener('resize', handleResize);
        handleResize();

        return () => viewport.removeEventListener('resize', handleResize);
      }
    };

    handleViewportChange();

    // Prevent pinch zoom on mobile
    const preventZoom = (e: TouchEvent) => {
      if (e.touches.length > 1) {
        e.preventDefault();
      }
    };

    document.addEventListener('touchstart', preventZoom, { passive: false });

    return () => {
      document.removeEventListener('touchstart', preventZoom);
    };
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <PWAInstallProvider>
        <AuthProvider>
          <WebSocketProvider>
            <Router>
              <Routes>
                {/* Public routes */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

                {/* Protected routes */}
                <Route
                  path="/*"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Routes>
                          <Route path="/" element={<Navigate to="/dashboard" replace />} />
                          <Route path="/dashboard" element={<DashboardPage />} />
                          <Route path="/artifacts" element={<ArtifactsPage />} />
                          <Route path="/artifacts/:id" element={<ArtifactDetailPage />} />
                          <Route path="/upload" element={<UploadPage />} />
                          <Route path="/agents" element={<AgentMonitorPage />} />
                          <Route path="/settings" element={<SettingsPage />} />
                        </Routes>
                      </Layout>
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </Router>

            {/* Mobile-optimized toast notifications */}
            <ToastContainer
              position={window.innerWidth < 600 ? "bottom-center" : "top-right"}
              autoClose={4000}
              hideProgressBar={false}
              newestOnTop={false}
              closeOnClick
              rtl={false}
              pauseOnFocusLoss
              draggable
              pauseOnHover
              theme="light"
              style={{
                fontSize: '14px',
                zIndex: 9999,
              }}
              toastStyle={{
                borderRadius: '8px',
                padding: '12px',
              }}
            />
          </WebSocketProvider>
        </AuthProvider>
      </PWAInstallProvider>
    </ThemeProvider>
  );
};

export default App;