import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Email,
  Lock,
  Person,
  Login as LoginIcon,
  PersonAdd as PersonAddIcon,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
  </div>
);

const Login: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { login, register, isLoading, error } = useAuth();

  const [tabValue, setTabValue] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  });

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setFormData({ name: '', email: '', password: '' });
  };

  const handleInputChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (tabValue === 0) {
        // Login
        await login({ email: formData.email, password: formData.password });
      } else {
        // Register
        await register({
          name: formData.name,
          email: formData.email,
          password: formData.password
        });
      }
      navigate('/dashboard');
    } catch (err) {
      // Error is handled by Redux
    }
  };

  const ArtifactorLogo = () => (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2, mb: 4 }}>
      <Box
        sx={{
          width: 60,
          height: 60,
          borderRadius: '16px',
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #c084fc 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 8px 32px rgba(99, 102, 241, 0.3)',
        }}
      >
        <Typography
          variant="h4"
          sx={{
            color: 'white',
            fontWeight: 700,
          }}
        >
          A
        </Typography>
      </Box>
      <Box>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #c084fc 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          ARTIFACTOR
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ fontWeight: 500 }}
        >
          Enterprise Artifact Management
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <Card
        sx={{
          width: '100%',
          maxWidth: 480,
          background: alpha(theme.palette.background.paper, 0.9),
          backdropFilter: 'blur(20px)',
          border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          borderRadius: '20px',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
        }}
      >
        <CardContent sx={{ p: 4 }}>
          <ArtifactorLogo />

          <Typography
            variant="h5"
            sx={{
              fontWeight: 600,
              textAlign: 'center',
              mb: 1,
              color: theme.palette.text.primary,
            }}
          >
            Welcome to ARTIFACTOR
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ textAlign: 'center', mb: 4 }}
          >
            Sign in to access your enterprise artifact management platform
          </Typography>

          {error && (
            <Alert
              severity="error"
              sx={{
                mb: 3,
                backgroundColor: alpha(theme.palette.error.main, 0.1),
                border: `1px solid ${alpha(theme.palette.error.main, 0.3)}`,
                borderRadius: '8px',
              }}
            >
              {error}
            </Alert>
          )}

          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            variant="fullWidth"
            sx={{
              mb: 2,
              '& .MuiTabs-indicator': {
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                height: 3,
                borderRadius: '2px',
              },
            }}
          >
            <Tab
              label="Sign In"
              icon={<LoginIcon />}
              iconPosition="start"
              sx={{
                textTransform: 'none',
                fontWeight: 600,
                gap: 1,
                color: tabValue === 0 ? theme.palette.primary.main : theme.palette.text.secondary,
              }}
            />
            <Tab
              label="Sign Up"
              icon={<PersonAddIcon />}
              iconPosition="start"
              sx={{
                textTransform: 'none',
                fontWeight: 600,
                gap: 1,
                color: tabValue === 1 ? theme.palette.primary.main : theme.palette.text.secondary,
              }}
            />
          </Tabs>

          <form onSubmit={handleSubmit}>
            <TabPanel value={tabValue} index={0}>
              {/* Login Form */}
              <TextField
                fullWidth
                label="Email Address"
                type="email"
                value={formData.email}
                onChange={handleInputChange('email')}
                required
                sx={{ mb: 3 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Email color="action" />
                    </InputAdornment>
                  ),
                }}
              />
              <TextField
                fullWidth
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={handleInputChange('password')}
                required
                sx={{ mb: 4 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              {/* Register Form */}
              <TextField
                fullWidth
                label="Full Name"
                value={formData.name}
                onChange={handleInputChange('name')}
                required
                sx={{ mb: 3 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Person color="action" />
                    </InputAdornment>
                  ),
                }}
              />
              <TextField
                fullWidth
                label="Email Address"
                type="email"
                value={formData.email}
                onChange={handleInputChange('email')}
                required
                sx={{ mb: 3 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Email color="action" />
                    </InputAdornment>
                  ),
                }}
              />
              <TextField
                fullWidth
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={handleInputChange('password')}
                required
                sx={{ mb: 4 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </TabPanel>

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={isLoading}
              sx={{
                py: 1.5,
                borderRadius: '12px',
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                boxShadow: '0 8px 24px rgba(99, 102, 241, 0.3)',
                textTransform: 'none',
                fontWeight: 600,
                fontSize: '1.1rem',
                '&:hover': {
                  background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                  boxShadow: '0 12px 32px rgba(99, 102, 241, 0.4)',
                  transform: 'translateY(-1px)',
                },
                '&:disabled': {
                  background: alpha(theme.palette.primary.main, 0.5),
                },
              }}
            >
              {isLoading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                tabValue === 0 ? 'Sign In' : 'Create Account'
              )}
            </Button>
          </form>

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ textAlign: 'center', mt: 3 }}
          >
            {tabValue === 0 ? "Don't have an account? " : "Already have an account? "}
            <Button
              variant="text"
              onClick={() => setTabValue(tabValue === 0 ? 1 : 0)}
              sx={{
                textTransform: 'none',
                fontWeight: 600,
                color: theme.palette.primary.main,
                p: 0,
                minWidth: 'auto',
                '&:hover': {
                  backgroundColor: 'transparent',
                  textDecoration: 'underline',
                },
              }}
            >
              {tabValue === 0 ? 'Sign up here' : 'Sign in here'}
            </Button>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Login;