import React, { useState } from 'react';
import {
  Sheet,
  SwipeableDrawer,
  Box,
  Typography,
  IconButton,
  Avatar,
  Chip,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Fab,
  Badge,
  Divider,
  useTheme,
} from '@mui/material';
import {
  Close as CloseIcon,
  People as PeopleIcon,
  VideoCall as VideoCallIcon,
  Chat as ChatIcon,
  Share as ShareIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useTouchGestures } from '../../hooks/useTouchGestures';

interface CollaboratorData {
  id: string;
  name: string;
  avatar: string;
  status: 'online' | 'away' | 'offline';
  role: 'editor' | 'viewer' | 'admin';
  lastSeen: Date;
  isTyping?: boolean;
  cursor?: { x: number; y: number };
}

interface MobileCollaborationSheetProps {
  open: boolean;
  onClose: () => void;
  collaborators: CollaboratorData[];
  onStartVideoCall: () => void;
  onOpenChat: () => void;
  onShareArtifact: () => void;
}

export const MobileCollaborationSheet: React.FC<MobileCollaborationSheetProps> = ({
  open,
  onClose,
  collaborators,
  onStartVideoCall,
  onOpenChat,
  onShareArtifact,
}) => {
  const theme = useTheme();
  const [dragPosition, setDragPosition] = useState(0);

  // Touch gestures for sheet interaction
  const bind = useTouchGestures({
    onSwipeDown: () => {
      if (dragPosition > 100) {
        onClose();
      }
    },
  });

  const getStatusColor = (status: CollaboratorData['status']) => {
    switch (status) {
      case 'online':
        return theme.palette.success.main;
      case 'away':
        return theme.palette.warning.main;
      case 'offline':
        return theme.palette.grey[400];
      default:
        return theme.palette.grey[400];
    }
  };

  const getRoleIcon = (role: CollaboratorData['role']) => {
    switch (role) {
      case 'editor':
        return <EditIcon fontSize="small" />;
      case 'viewer':
        return <ViewIcon fontSize="small" />;
      case 'admin':
        return <EditIcon fontSize="small" color="primary" />;
      default:
        return <ViewIcon fontSize="small" />;
    }
  };

  const onlineCollaborators = collaborators.filter(c => c.status === 'online');
  const totalCollaborators = collaborators.length;

  return (
    <SwipeableDrawer
      anchor="bottom"
      open={open}
      onClose={onClose}
      onOpen={() => {}}
      disableSwipeToOpen
      PaperProps={{
        sx: {
          borderTopLeftRadius: 16,
          borderTopRightRadius: 16,
          maxHeight: '80vh',
          backgroundColor: theme.palette.background.paper,
        },
      }}
      {...bind()}
    >
      <Box sx={{ p: 2 }}>
        {/* Handle */}
        <Box
          sx={{
            width: 40,
            height: 4,
            backgroundColor: theme.palette.grey[300],
            borderRadius: 2,
            mx: 'auto',
            mb: 2,
            cursor: 'grab',
          }}
        />

        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <PeopleIcon color="primary" />
            <Typography variant="h6" component="div">
              Collaboration
            </Typography>
            <Badge badgeContent={onlineCollaborators.length} color="success">
              <Chip
                label={`${totalCollaborators} active`}
                size="small"
                variant="outlined"
              />
            </Badge>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Quick Actions */}
        <Box sx={{ display: 'flex', gap: 1, mb: 3, overflowX: 'auto', pb: 1 }}>
          <motion.div whileTap={{ scale: 0.95 }}>
            <Fab
              variant="extended"
              size="small"
              color="primary"
              onClick={onStartVideoCall}
              sx={{ minWidth: 120, flexShrink: 0 }}
            >
              <VideoCallIcon sx={{ mr: 1 }} />
              Video Call
            </Fab>
          </motion.div>

          <motion.div whileTap={{ scale: 0.95 }}>
            <Fab
              variant="extended"
              size="small"
              onClick={onOpenChat}
              sx={{
                minWidth: 100,
                flexShrink: 0,
                backgroundColor: theme.palette.grey[100],
                color: theme.palette.text.primary,
                '&:hover': {
                  backgroundColor: theme.palette.grey[200],
                },
              }}
            >
              <ChatIcon sx={{ mr: 1 }} />
              Chat
            </Fab>
          </motion.div>

          <motion.div whileTap={{ scale: 0.95 }}>
            <Fab
              variant="extended"
              size="small"
              onClick={onShareArtifact}
              sx={{
                minWidth: 100,
                flexShrink: 0,
                backgroundColor: theme.palette.grey[100],
                color: theme.palette.text.primary,
                '&:hover': {
                  backgroundColor: theme.palette.grey[200],
                },
              }}
            >
              <ShareIcon sx={{ mr: 1 }} />
              Share
            </Fab>
          </motion.div>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Collaborators List */}
        <Typography variant="subtitle2" sx={{ mb: 1, color: theme.palette.text.secondary }}>
          Active Collaborators
        </Typography>

        <List sx={{ maxHeight: 400, overflow: 'auto' }}>
          <AnimatePresence>
            {collaborators.map((collaborator, index) => (
              <motion.div
                key={collaborator.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.1 }}
              >
                <ListItem
                  sx={{
                    borderRadius: 2,
                    mb: 1,
                    backgroundColor: collaborator.status === 'online'
                      ? 'rgba(76, 175, 80, 0.05)'
                      : 'transparent',
                    border: collaborator.status === 'online'
                      ? `1px solid rgba(76, 175, 80, 0.2)`
                      : 'none',
                  }}
                >
                  <ListItemAvatar>
                    <Badge
                      overlap="circular"
                      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                      badgeContent={
                        <Box
                          sx={{
                            width: 12,
                            height: 12,
                            borderRadius: '50%',
                            backgroundColor: getStatusColor(collaborator.status),
                            border: `2px solid ${theme.palette.background.paper}`,
                          }}
                        />
                      }
                    >
                      <Avatar
                        src={collaborator.avatar}
                        sx={{
                          width: 40,
                          height: 40,
                          backgroundColor: theme.palette.primary.main,
                        }}
                      >
                        {collaborator.name.charAt(0).toUpperCase()}
                      </Avatar>
                    </Badge>
                  </ListItemAvatar>

                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" fontWeight={500}>
                          {collaborator.name}
                        </Typography>
                        {collaborator.isTyping && (
                          <motion.div
                            animate={{ opacity: [0.5, 1, 0.5] }}
                            transition={{ repeat: Infinity, duration: 1.5 }}
                          >
                            <Chip
                              label="typing..."
                              size="small"
                              sx={{
                                height: 20,
                                fontSize: '0.6rem',
                                backgroundColor: theme.palette.primary.light,
                                color: 'white',
                              }}
                            />
                          </motion.div>
                        )}
                      </Box>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        <Chip
                          icon={getRoleIcon(collaborator.role)}
                          label={collaborator.role}
                          size="small"
                          variant="outlined"
                          sx={{ height: 24, fontSize: '0.7rem' }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {collaborator.status === 'online'
                            ? 'Active now'
                            : `Last seen ${collaborator.lastSeen.toLocaleTimeString()}`
                          }
                        </Typography>
                      </Box>
                    }
                  />

                  <ListItemSecondaryAction>
                    {collaborator.status === 'online' && (
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ repeat: Infinity, duration: 2 }}
                      >
                        <IconButton
                          edge="end"
                          size="small"
                          sx={{
                            backgroundColor: theme.palette.success.light,
                            color: 'white',
                            '&:hover': {
                              backgroundColor: theme.palette.success.main,
                            },
                          }}
                        >
                          <VideoCallIcon fontSize="small" />
                        </IconButton>
                      </motion.div>
                    )}
                  </ListItemSecondaryAction>
                </ListItem>
              </motion.div>
            ))}
          </AnimatePresence>
        </List>

        {/* Empty State */}
        {collaborators.length === 0 && (
          <Box
            sx={{
              textAlign: 'center',
              py: 4,
              color: theme.palette.text.secondary,
            }}
          >
            <PeopleIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
            <Typography variant="body2">
              No active collaborators
            </Typography>
            <Typography variant="caption">
              Share this artifact to start collaborating
            </Typography>
          </Box>
        )}
      </Box>
    </SwipeableDrawer>
  );
};