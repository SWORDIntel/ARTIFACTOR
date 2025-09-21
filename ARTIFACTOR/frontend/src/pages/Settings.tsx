import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  Divider,
  Avatar,
  Button,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Person as PersonIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Palette as PaletteIcon,
} from '@mui/icons-material';

const Settings: React.FC = () => {
  const theme = useTheme();

  return (
    <Box>
      <Typography
        variant="h4"
        sx={{
          fontWeight: 700,
          mb: 1,
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #c084fc 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}
      >
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Customize your ARTIFACTOR experience
      </Typography>

      <Card
        sx={{
          background: alpha(theme.palette.background.paper, 0.8),
          backdropFilter: 'blur(20px)',
          border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          borderRadius: '16px',
        }}
      >
        <CardContent sx={{ p: 4 }}>
          {/* Profile Section */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
            <PersonIcon sx={{ color: theme.palette.primary.main }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Profile
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 4 }}>
            <Avatar
              sx={{
                width: 80,
                height: 80,
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                fontSize: '2rem',
                fontWeight: 700,
              }}
            >
              U
            </Avatar>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                User Name
              </Typography>
              <Typography variant="body2" color="text.secondary">
                user@example.com
              </Typography>
              <Button variant="outlined" size="small" sx={{ mt: 1, borderRadius: '8px' }}>
                Edit Profile
              </Button>
            </Box>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Theme Section */}
          <Box sx={{ mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <PaletteIcon sx={{ color: theme.palette.primary.main }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Appearance
              </Typography>
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body1" sx={{ fontWeight: 500, mb: 1 }}>
                Theme Preference
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                You've chosen the perfect dark theme! No light mode available - dark themes only!
              </Typography>
              <Box
                sx={{
                  p: 2,
                  borderRadius: '8px',
                  background: alpha(theme.palette.primary.main, 0.1),
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
                }}
              >
                <Typography variant="body2" sx={{ fontWeight: 600, color: theme.palette.primary.main }}>
                  🌙 Dark Mode Active
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Beautiful dark theme optimized for your eyes and productivity
                </Typography>
              </Box>
            </Box>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Notifications Section */}
          <Box sx={{ mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <NotificationsIcon sx={{ color: theme.palette.primary.main }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Notifications
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Email notifications"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Push notifications"
              />
              <FormControlLabel
                control={<Switch />}
                label="SMS notifications"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Collaboration updates"
              />
            </Box>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Security Section */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <SecurityIcon sx={{ color: theme.palette.primary.main }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Security
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Two-factor authentication"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Login notifications"
              />
              <FormControlLabel
                control={<Switch />}
                label="API access logging"
              />
              
              <Box sx={{ mt: 2 }}>
                <Button variant="outlined" sx={{ mr: 2, borderRadius: '8px' }}>
                  Change Password
                </Button>
                <Button variant="outlined" sx={{ borderRadius: '8px' }}>
                  Download Data
                </Button>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Settings;