import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Avatar,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Group as GroupIcon,
  Circle as CircleIcon,
  VideoCall as VideoCallIcon,
  Chat as ChatIcon,
} from '@mui/icons-material';

const Collaboration: React.FC = () => {
  const theme = useTheme();

  const mockCollaborators = [
    { id: '1', name: 'John Doe', status: 'online', avatar: '', role: 'Owner' },
    { id: '2', name: 'Jane Smith', status: 'online', avatar: '', role: 'Editor' },
    { id: '3', name: 'Bob Wilson', status: 'away', avatar: '', role: 'Viewer' },
  ];

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
        Real-time Collaboration
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Collaborate with your team in real-time with live presence and WebSocket sync
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card
            sx={{
              background: alpha(theme.palette.background.paper, 0.8),
              backdropFilter: 'blur(20px)',
              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              borderRadius: '16px',
              mb: 3,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Active Collaboration Session
              </Typography>
              <Box
                sx={{
                  height: 400,
                  background: alpha(theme.palette.primary.main, 0.05),
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: `2px dashed ${alpha(theme.palette.primary.main, 0.3)}`,
                }}
              >
                <Box sx={{ textAlign: 'center' }}>
                  <VideoCallIcon sx={{ fontSize: 48, color: theme.palette.primary.main, mb: 2 }} />
                  <Typography variant="h6" color="primary">
                    Join Collaboration Session
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    WebSocket real-time editing with live cursors
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            sx={{
              background: alpha(theme.palette.background.paper, 0.8),
              backdropFilter: 'blur(20px)',
              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              borderRadius: '16px',
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Online Collaborators
              </Typography>
              <List>
                {mockCollaborators.map((user) => (
                  <ListItem key={user.id} sx={{ px: 0 }}>
                    <ListItemAvatar>
                      <Box sx={{ position: 'relative' }}>
                        <Avatar
                          sx={{
                            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                          }}
                        >
                          {user.name[0]}
                        </Avatar>
                        <CircleIcon
                          sx={{
                            position: 'absolute',
                            bottom: 0,
                            right: 0,
                            fontSize: 12,
                            color: user.status === 'online' ? theme.palette.success.main : theme.palette.warning.main,
                          }}
                        />
                      </Box>
                    </ListItemAvatar>
                    <ListItemText
                      primary={user.name}
                      secondary={
                        <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                          <Chip
                            label={user.role}
                            size="small"
                            sx={{
                              background: alpha(theme.palette.primary.main, 0.1),
                              color: theme.palette.primary.main,
                            }}
                          />
                          <Chip
                            label={user.status}
                            size="small"
                            sx={{
                              background: alpha(
                                user.status === 'online' ? theme.palette.success.main : theme.palette.warning.main,
                                0.1
                              ),
                              color: user.status === 'online' ? theme.palette.success.main : theme.palette.warning.main,
                            }}
                          />
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Collaboration;