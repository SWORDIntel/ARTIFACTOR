/**
 * Presence indicator component for ARTIFACTOR v3.0
 * Shows real-time user cursors, selections, and activity indicators
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Chip,
  Avatar,
  Tooltip,
  Fade,
  Paper,
  Typography,
  styled
} from '@mui/material';
import { useCollaboration, type ActiveUser } from './CollaborationProvider';

interface PresenceIndicatorProps {
  className?: string;
}

interface CursorProps {
  user: ActiveUser;
  position: { x: number; y: number };
}

const CursorContainer = styled(Box)(({ theme }) => ({
  position: 'absolute',
  pointerEvents: 'none',
  zIndex: 1000,
  transition: 'all 0.1s ease-out'
}));

const CursorLine = styled(Box)<{ color: string }>(({ color }) => ({
  width: '2px',
  height: '20px',
  backgroundColor: color,
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    width: 0,
    height: 0,
    borderLeft: '4px solid transparent',
    borderRight: '4px solid transparent',
    borderTop: `6px solid ${color}`,
    transform: 'translateX(-3px) translateY(-6px)'
  }
}));

const CursorLabel = styled(Paper)<{ color: string }>(({ color, theme }) => ({
  position: 'absolute',
  top: '-30px',
  left: '8px',
  padding: '2px 6px',
  backgroundColor: color,
  color: 'white',
  fontSize: '12px',
  borderRadius: '4px',
  whiteSpace: 'nowrap',
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '100%',
    left: '8px',
    width: 0,
    height: 0,
    borderLeft: '4px solid transparent',
    borderRight: '4px solid transparent',
    borderTop: `4px solid ${color}`
  }
}));

const SelectionOverlay = styled(Box)<{ color: string }>(({ color }) => ({
  position: 'absolute',
  backgroundColor: `${color}33`,
  border: `1px solid ${color}`,
  pointerEvents: 'none',
  zIndex: 999
}));

const TypingIndicator = styled(Chip)(({ theme }) => ({
  position: 'fixed',
  bottom: theme.spacing(2),
  left: theme.spacing(2),
  zIndex: 1001,
  animation: 'pulse 1.5s infinite'
}));

// User color palette for consistent visual identity
const USER_COLORS = [
  '#2196F3', // Blue
  '#4CAF50', // Green
  '#FF9800', // Orange
  '#9C27B0', // Purple
  '#F44336', // Red
  '#00BCD4', // Cyan
  '#795548', // Brown
  '#607D8B', // Blue Grey
  '#3F51B5', // Indigo
  '#009688'  // Teal
];

const getUserColor = (userId: string): string => {
  // Generate consistent color based on user ID
  let hash = 0;
  for (let i = 0; i < userId.length; i++) {
    hash = ((hash << 5) - hash) + userId.charCodeAt(i);
    hash = hash & hash; // Convert to 32-bit integer
  }
  return USER_COLORS[Math.abs(hash) % USER_COLORS.length];
};

const Cursor: React.FC<CursorProps> = ({ user, position }) => {
  const color = getUserColor(user.user_id);
  const displayName = user.user_data.display_name || user.user_data.username;

  return (
    <CursorContainer style={{ left: position.x, top: position.y }}>
      <CursorLine color={color} />
      <CursorLabel color={color} elevation={2}>
        {displayName}
      </CursorLabel>
    </CursorContainer>
  );
};

export const PresenceIndicator: React.FC<PresenceIndicatorProps> = ({ className }) => {
  const { activeUsers, currentUser, typingUsers, isConnected } = useCollaboration();
  const [cursors, setCursors] = useState<Map<string, { x: number; y: number }>>(new Map());
  const [selections, setSelections] = useState<Map<string, any>>(new Map());

  // Filter out current user from presence indicators
  const otherUsers = activeUsers.filter(user => user.user_id !== currentUser?.id);

  // Update cursors when active users change
  useEffect(() => {
    const newCursors = new Map();
    const newSelections = new Map();

    otherUsers.forEach(user => {
      if (user.cursor) {
        // Convert line/column to pixel coordinates
        // This would need to be implemented based on your editor
        const x = user.cursor.column * 8; // Approximate character width
        const y = user.cursor.line * 20; // Approximate line height
        newCursors.set(user.user_id, { x, y });
      }

      if (user.selection) {
        newSelections.set(user.user_id, user.selection);
      }
    });

    setCursors(newCursors);
    setSelections(newSelections);
  }, [otherUsers]);

  // Typing users display
  const typingUsersData = otherUsers.filter(user => typingUsers.includes(user.user_id));

  return (
    <Box className={className}>
      {/* Connection status indicator */}
      {!isConnected && (
        <Chip
          label="Reconnecting..."
          color="warning"
          size="small"
          sx={{
            position: 'fixed',
            top: 16,
            right: 16,
            zIndex: 1002
          }}
        />
      )}

      {/* Active users overview */}
      {otherUsers.length > 0 && (
        <Box
          sx={{
            position: 'fixed',
            top: 16,
            left: 16,
            zIndex: 1001,
            display: 'flex',
            gap: 1,
            alignItems: 'center'
          }}
        >
          <Typography variant="caption" sx={{ mr: 1 }}>
            Active:
          </Typography>
          {otherUsers.slice(0, 5).map(user => {
            const color = getUserColor(user.user_id);
            return (
              <Tooltip
                key={user.user_id}
                title={`${user.user_data.display_name || user.user_data.username} - ${user.activity || 'viewing'}`}
                arrow
              >
                <Avatar
                  sx={{
                    width: 24,
                    height: 24,
                    fontSize: '0.75rem',
                    backgroundColor: color,
                    border: user.status === 'active' ? `2px solid ${color}` : '2px solid #ccc'
                  }}
                >
                  {(user.user_data.display_name || user.user_data.username).charAt(0).toUpperCase()}
                </Avatar>
              </Tooltip>
            );
          })}
          {otherUsers.length > 5 && (
            <Chip
              label={`+${otherUsers.length - 5}`}
              size="small"
              variant="outlined"
            />
          )}
        </Box>
      )}

      {/* Render cursors */}
      {Array.from(cursors.entries()).map(([userId, position]) => {
        const user = otherUsers.find(u => u.user_id === userId);
        if (!user) return null;

        return (
          <Cursor
            key={userId}
            user={user}
            position={position}
          />
        );
      })}

      {/* Render selections */}
      {Array.from(selections.entries()).map(([userId, selection]) => {
        const user = otherUsers.find(u => u.user_id === userId);
        if (!user || !selection.start || !selection.end) return null;

        const color = getUserColor(userId);

        // Convert selection to pixel coordinates
        // This would need to be implemented based on your editor
        const startX = selection.start.column * 8;
        const startY = selection.start.line * 20;
        const endX = selection.end.column * 8;
        const endY = selection.end.line * 20;

        return (
          <SelectionOverlay
            key={`selection-${userId}`}
            color={color}
            style={{
              left: Math.min(startX, endX),
              top: Math.min(startY, endY),
              width: Math.abs(endX - startX),
              height: Math.abs(endY - startY) || 20
            }}
          />
        );
      })}

      {/* Typing indicators */}
      {typingUsersData.length > 0 && (
        <Fade in timeout={300}>
          <TypingIndicator
            label={
              typingUsersData.length === 1
                ? `${typingUsersData[0].user_data.display_name || typingUsersData[0].user_data.username} is typing...`
                : `${typingUsersData.length} users are typing...`
            }
            color="primary"
            variant="filled"
          />
        </Fade>
      )}

      {/* Add global styles for pulse animation */}
      <style jsx global>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.7; }
          100% { opacity: 1; }
        }
      `}</style>
    </Box>
  );
};