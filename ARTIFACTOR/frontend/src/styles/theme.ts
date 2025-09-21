import { createTheme, Theme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';

// ARTIFACTOR Dark Theme - Beautiful Dark Blue/Purple Scheme
// User specifically requested NO light theme - dark only!

export const darkTheme: Theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#6366f1', // Indigo-500
      light: '#818cf8', // Indigo-400
      dark: '#4f46e5', // Indigo-600
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#8b5cf6', // Violet-500
      light: '#a78bfa', // Violet-400
      dark: '#7c3aed', // Violet-600
      contrastText: '#ffffff',
    },
    background: {
      default: '#0f0f23', // Very dark navy
      paper: '#1a1a2e', // Dark navy-purple
    },
    surface: {
      main: '#16213e', // Dark blue surface
      light: '#1e2749', // Lighter blue surface
      dark: '#0f1419', // Darker surface
    },
    text: {
      primary: '#e2e8f0', // Light gray
      secondary: '#cbd5e1', // Medium gray
      disabled: '#64748b', // Dark gray
    },
    divider: alpha('#475569', 0.3), // Subtle gray divider
    error: {
      main: '#ef4444', // Red-500
      light: '#f87171', // Red-400
      dark: '#dc2626', // Red-600
    },
    warning: {
      main: '#f59e0b', // Amber-500
      light: '#fbbf24', // Amber-400
      dark: '#d97706', // Amber-600
    },
    info: {
      main: '#06b6d4', // Cyan-500
      light: '#22d3ee', // Cyan-400
      dark: '#0891b2', // Cyan-600
    },
    success: {
      main: '#10b981', // Emerald-500
      light: '#34d399', // Emerald-400
      dark: '#059669', // Emerald-600
    },
    // Custom colors for ARTIFACTOR
    custom: {
      accent: '#c084fc', // Purple-400 - for highlights
      gradient: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #c084fc 100%)',
      cardBg: alpha('#1a1a2e', 0.8),
      hoverBg: alpha('#16213e', 0.9),
      glassBg: alpha('#1a1a2e', 0.7),
    },
  },
  typography: {
    fontFamily: '"Inter", "Segoe UI", "Roboto", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #c084fc 100%)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      lineHeight: 1.3,
      color: '#e2e8f0',
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
      color: '#e2e8f0',
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
      color: '#cbd5e1',
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 500,
      lineHeight: 1.4,
      color: '#cbd5e1',
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.4,
      color: '#cbd5e1',
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      color: '#cbd5e1',
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
      color: '#94a3b8',
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
    caption: {
      fontSize: '0.75rem',
      color: '#64748b',
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#0f0f23',
          background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%)',
          minHeight: '100vh',
          scrollbarWidth: 'thin',
          scrollbarColor: '#475569 #1e293b',
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#1e293b',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#475569',
            borderRadius: '4px',
            '&:hover': {
              background: '#64748b',
            },
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: alpha('#1a1a2e', 0.8),
          backdropFilter: 'blur(20px)',
          border: `1px solid ${alpha('#475569', 0.2)}`,
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
          transition: 'all 0.3s ease-in-out',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 12px 40px rgba(99, 102, 241, 0.2)',
            border: `1px solid ${alpha('#6366f1', 0.3)}`,
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          textTransform: 'none',
          fontWeight: 600,
          padding: '10px 24px',
          transition: 'all 0.2s ease-in-out',
        },
        contained: {
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
          boxShadow: '0 4px 16px rgba(99, 102, 241, 0.3)',
          '&:hover': {
            background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
            boxShadow: '0 6px 20px rgba(99, 102, 241, 0.4)',
            transform: 'translateY(-1px)',
          },
        },
        outlined: {
          borderColor: alpha('#6366f1', 0.5),
          color: '#6366f1',
          '&:hover': {
            borderColor: '#6366f1',
            backgroundColor: alpha('#6366f1', 0.1),
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: alpha('#1a1a2e', 0.9),
          backdropFilter: 'blur(20px)',
          borderBottom: `1px solid ${alpha('#475569', 0.2)}`,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          background: alpha('#1a1a2e', 0.95),
          backdropFilter: 'blur(20px)',
          borderRight: `1px solid ${alpha('#475569', 0.2)}`,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: alpha('#16213e', 0.5),
            borderRadius: '8px',
            '& fieldset': {
              borderColor: alpha('#475569', 0.3),
            },
            '&:hover fieldset': {
              borderColor: alpha('#6366f1', 0.5),
            },
            '&.Mui-focused fieldset': {
              borderColor: '#6366f1',
              boxShadow: `0 0 0 2px ${alpha('#6366f1', 0.2)}`,
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          backgroundColor: alpha('#16213e', 0.8),
          color: '#cbd5e1',
          border: `1px solid ${alpha('#475569', 0.3)}`,
          '&:hover': {
            backgroundColor: alpha('#6366f1', 0.2),
          },
        },
        filled: {
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
          color: '#ffffff',
        },
      },
    },
    MuiDataGrid: {
      styleOverrides: {
        root: {
          backgroundColor: alpha('#1a1a2e', 0.8),
          border: `1px solid ${alpha('#475569', 0.2)}`,
          borderRadius: '12px',
          '& .MuiDataGrid-cell': {
            borderColor: alpha('#475569', 0.2),
            color: '#cbd5e1',
          },
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: alpha('#16213e', 0.8),
            borderColor: alpha('#475569', 0.2),
            color: '#e2e8f0',
          },
          '& .MuiDataGrid-row': {
            '&:hover': {
              backgroundColor: alpha('#6366f1', 0.1),
            },
            '&.Mui-selected': {
              backgroundColor: alpha('#6366f1', 0.2),
            },
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          background: alpha('#1a1a2e', 0.8),
          backdropFilter: 'blur(20px)',
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          background: alpha('#1a1a2e', 0.95),
          backdropFilter: 'blur(20px)',
          border: `1px solid ${alpha('#475569', 0.2)}`,
          borderRadius: '8px',
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: alpha('#0f1419', 0.9),
          backdropFilter: 'blur(10px)',
          border: `1px solid ${alpha('#475569', 0.3)}`,
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          minHeight: '48px',
        },
        indicator: {
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
          height: '3px',
          borderRadius: '2px',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          color: '#94a3b8',
          '&.Mui-selected': {
            color: '#6366f1',
          },
        },
      },
    },
  },
});

// Custom theme augmentation for TypeScript
declare module '@mui/material/styles' {
  interface Palette {
    surface: {
      main: string;
      light: string;
      dark: string;
    };
    custom: {
      accent: string;
      gradient: string;
      cardBg: string;
      hoverBg: string;
      glassBg: string;
    };
  }

  interface PaletteOptions {
    surface?: {
      main: string;
      light: string;
      dark: string;
    };
    custom?: {
      accent: string;
      gradient: string;
      cardBg: string;
      hoverBg: string;
      glassBg: string;
    };
  }
}

export default darkTheme;