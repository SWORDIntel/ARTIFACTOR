/**
 * Collaboration sidebar for ARTIFACTOR v3.0
 * Displays active users, comments, activity feed, and notifications
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  Tab,
  Tabs,
  Badge,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Chip,
  IconButton,
  TextField,
  Button,
  Paper,
  Divider,
  Tooltip,
  Menu,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  People as PeopleIcon,
  Comment as CommentIcon,
  Timeline as ActivityIcon,
  Notifications as NotificationsIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Reply as ReplyIcon,
  ExpandMore as ExpandMoreIcon,
  Check as CheckIcon,
  Circle as CircleIcon
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { useCollaboration, type ActiveUser, type Comment, type Activity, type Notification } from './CollaborationProvider';

interface CollaborationSidebarProps {
  width?: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`collaboration-tabpanel-${index}`}
      aria-labelledby={`collaboration-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 2 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

export const CollaborationSidebar: React.FC<CollaborationSidebarProps> = ({ width = 350 }) => {
  const {
    isConnected,
    activeUsers,
    currentUser,
    typingUsers,
    comments,
    activities,
    notifications,
    notificationCounts,
    addComment,
    updateComment,
    deleteComment,
    markNotificationRead,
    markAllNotificationsRead
  } = useCollaboration();

  const [currentTab, setCurrentTab] = useState(0);
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [editingComment, setEditingComment] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedComment, setSelectedComment] = useState<string | null>(null);

  const commentInputRef = useRef<HTMLInputElement>(null);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleCommentSubmit = async () => {
    if (!newComment.trim()) return;

    try {
      await addComment(newComment, replyingTo || undefined);
      setNewComment('');
      setReplyingTo(null);
    } catch (error) {
      console.error('Failed to add comment:', error);
    }
  };

  const handleEditComment = async (commentId: string) => {
    if (!editText.trim()) return;

    try {
      await updateComment(commentId, editText);
      setEditingComment(null);
      setEditText('');
    } catch (error) {
      console.error('Failed to update comment:', error);
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    try {
      await deleteComment(commentId);
      setAnchorEl(null);
      setSelectedComment(null);
    } catch (error) {
      console.error('Failed to delete comment:', error);
    }
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, commentId: string) => {
    setAnchorEl(event.currentTarget);
    setSelectedComment(commentId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedComment(null);
  };

  const startEdit = (comment: Comment) => {
    setEditingComment(comment.id);
    setEditText(comment.content);
    handleMenuClose();
  };

  const startReply = (commentId: string) => {
    setReplyingTo(commentId);
    handleMenuClose();
    if (commentInputRef.current) {
      commentInputRef.current.focus();
    }
  };

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.read) {
      await markNotificationRead(notification.id);
    }

    // Navigate to related content if applicable
    if (notification.related_comment_id && notification.artifact_id) {
      // Scroll to comment or show comment context
      console.log('Navigate to comment:', notification.related_comment_id);
    }
  };

  // Users presence status indicator
  const getPresenceColor = (user: ActiveUser): string => {
    switch (user.status) {
      case 'active': return '#4caf50';
      case 'away': return '#ff9800';
      case 'offline': return '#9e9e9e';
      default: return '#9e9e9e';
    }
  };

  // Render active users tab
  const renderUsersTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Active Users ({activeUsers.length})
      </Typography>

      {!isConnected && (
        <Typography variant="body2" color="error" sx={{ mb: 2 }}>
          Connection lost. Attempting to reconnect...
        </Typography>
      )}

      <List>
        {activeUsers.map((user) => (
          <ListItem key={user.user_id}>
            <ListItemAvatar>
              <Badge
                overlap="circular"
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                badgeContent={
                  <CircleIcon
                    sx={{
                      color: getPresenceColor(user),
                      fontSize: 12,
                      border: '2px solid white',
                      borderRadius: '50%'
                    }}
                  />
                }
              >
                <Avatar sx={{ width: 32, height: 32 }}>
                  {user.user_data.username?.charAt(0).toUpperCase()}
                </Avatar>
              </Badge>
            </ListItemAvatar>
            <ListItemText
              primary={user.user_data.display_name || user.user_data.username}
              secondary={
                <Box>
                  <Typography variant="caption" display="block">
                    {user.activity || 'Viewing'}
                  </Typography>
                  {typingUsers.includes(user.user_id) && (
                    <Chip
                      label="Typing..."
                      size="small"
                      color="primary"
                      sx={{ mt: 0.5 }}
                    />
                  )}
                </Box>
              }
            />
          </ListItem>
        ))}
      </List>

      {activeUsers.length === 0 && (
        <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', mt: 2 }}>
          No other users currently active
        </Typography>
      )}
    </Box>
  );

  // Render comments tab
  const renderCommentsTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Comments ({comments.length})
      </Typography>

      {/* Add comment input */}
      <Paper sx={{ p: 2, mb: 2 }}>
        {replyingTo && (
          <Box sx={{ mb: 1 }}>
            <Chip
              label={`Replying to comment`}
              size="small"
              onDelete={() => setReplyingTo(null)}
              sx={{ mb: 1 }}
            />
          </Box>
        )}
        <TextField
          ref={commentInputRef}
          fullWidth
          multiline
          minRows={2}
          placeholder="Add a comment..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          sx={{ mb: 1 }}
        />
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
          {replyingTo && (
            <Button size="small" onClick={() => setReplyingTo(null)}>
              Cancel
            </Button>
          )}
          <Button
            variant="contained"
            size="small"
            onClick={handleCommentSubmit}
            disabled={!newComment.trim()}
          >
            {replyingTo ? 'Reply' : 'Comment'}
          </Button>
        </Box>
      </Paper>

      {/* Comments list */}
      <List sx={{ maxHeight: '60vh', overflow: 'auto' }}>
        {comments
          .filter(comment => !comment.parent_id) // Only show top-level comments
          .map((comment) => (
          <React.Fragment key={comment.id}>
            <ListItem alignItems="flex-start" sx={{ px: 0 }}>
              <ListItemAvatar>
                <Avatar sx={{ width: 32, height: 32 }}>
                  {comment.user.username.charAt(0).toUpperCase()}
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="subtitle2">
                      {comment.user.username}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Typography variant="caption" color="textSecondary">
                        {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}
                      </Typography>
                      {comment.user.id === currentUser?.id && (
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuClick(e, comment.id)}
                        >
                          <MoreVertIcon fontSize="small" />
                        </IconButton>
                      )}
                    </Box>
                  </Box>
                }
                secondary={
                  <Box sx={{ mt: 1 }}>
                    {editingComment === comment.id ? (
                      <Box>
                        <TextField
                          fullWidth
                          multiline
                          value={editText}
                          onChange={(e) => setEditText(e.target.value)}
                          sx={{ mb: 1 }}
                        />
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button
                            size="small"
                            variant="contained"
                            onClick={() => handleEditComment(comment.id)}
                          >
                            Save
                          </Button>
                          <Button
                            size="small"
                            onClick={() => {
                              setEditingComment(null);
                              setEditText('');
                            }}
                          >
                            Cancel
                          </Button>
                        </Box>
                      </Box>
                    ) : (
                      <Box>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                          {comment.content}
                        </Typography>
                        {comment.edited && (
                          <Typography variant="caption" color="textSecondary" sx={{ fontStyle: 'italic' }}>
                            (edited)
                          </Typography>
                        )}
                        <Box sx={{ mt: 1 }}>
                          <Button
                            size="small"
                            startIcon={<ReplyIcon />}
                            onClick={() => startReply(comment.id)}
                          >
                            Reply
                          </Button>
                        </Box>
                      </Box>
                    )}
                  </Box>
                }
              />
            </ListItem>

            {/* Render replies */}
            {comments
              .filter(reply => reply.parent_id === comment.id)
              .map((reply) => (
                <ListItem key={reply.id} sx={{ pl: 6, pr: 0 }} alignItems="flex-start">
                  <ListItemAvatar>
                    <Avatar sx={{ width: 24, height: 24 }}>
                      {reply.user.username.charAt(0).toUpperCase()}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Typography variant="caption" fontWeight="medium">
                          {reply.user.username}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {formatDistanceToNow(new Date(reply.created_at), { addSuffix: true })}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {reply.content}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}

            <Divider variant="inset" component="li" />
          </React.Fragment>
        ))}
      </List>

      {comments.length === 0 && (
        <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', mt: 2 }}>
          No comments yet. Start a conversation!
        </Typography>
      )}
    </Box>
  );

  // Render activity tab
  const renderActivityTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Activity ({activities.length})
      </Typography>

      <List sx={{ maxHeight: '70vh', overflow: 'auto' }}>
        {activities.map((activity) => (
          <ListItem key={activity.id} alignItems="flex-start">
            <ListItemAvatar>
              <Avatar sx={{ width: 32, height: 32 }}>
                {activity.user.username.charAt(0).toUpperCase()}
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={
                <Box>
                  <Typography variant="body2">
                    <strong>{activity.user.username}</strong> {activity.description}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                  </Typography>
                </Box>
              }
              secondary={
                activity.tags.length > 0 && (
                  <Box sx={{ mt: 0.5 }}>
                    {activity.tags.map((tag) => (
                      <Chip key={tag} label={tag} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                    ))}
                  </Box>
                )
              }
            />
          </ListItem>
        ))}
      </List>

      {activities.length === 0 && (
        <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', mt: 2 }}>
          No activity yet
        </Typography>
      )}
    </Box>
  );

  // Render notifications tab
  const renderNotificationsTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Notifications ({notificationCounts.unread})
        </Typography>
        {notificationCounts.unread > 0 && (
          <Button size="small" onClick={markAllNotificationsRead}>
            Mark all read
          </Button>
        )}
      </Box>

      <List sx={{ maxHeight: '70vh', overflow: 'auto' }}>
        {notifications.map((notification) => (
          <ListItem
            key={notification.id}
            button
            onClick={() => handleNotificationClick(notification)}
            sx={{
              bgcolor: notification.read ? 'transparent' : 'action.hover',
              borderRadius: 1,
              mb: 1
            }}
          >
            <ListItemAvatar>
              <Badge
                color={notification.priority === 'urgent' ? 'error' : 'primary'}
                variant={notification.read ? 'standard' : 'dot'}
              >
                <NotificationsIcon />
              </Badge>
            </ListItemAvatar>
            <ListItemText
              primary={notification.title}
              secondary={
                <Box>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    {notification.message}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                  </Typography>
                </Box>
              }
            />
            {!notification.read && (
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  markNotificationRead(notification.id);
                }}
              >
                <CheckIcon fontSize="small" />
              </IconButton>
            )}
          </ListItem>
        ))}
      </List>

      {notifications.length === 0 && (
        <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', mt: 2 }}>
          No notifications
        </Typography>
      )}
    </Box>
  );

  return (
    <Paper
      sx={{
        width,
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 0,
        borderLeft: '1px solid',
        borderColor: 'divider'
      }}
    >
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          variant="fullWidth"
          textColor="primary"
          indicatorColor="primary"
        >
          <Tab
            icon={<Badge badgeContent={activeUsers.length} color="primary"><PeopleIcon /></Badge>}
            aria-label="users"
          />
          <Tab
            icon={<Badge badgeContent={comments.length} color="primary"><CommentIcon /></Badge>}
            aria-label="comments"
          />
          <Tab
            icon={<Badge badgeContent={activities.length} color="primary"><ActivityIcon /></Badge>}
            aria-label="activity"
          />
          <Tab
            icon={<Badge badgeContent={notificationCounts.unread} color="error"><NotificationsIcon /></Badge>}
            aria-label="notifications"
          />
        </Tabs>
      </Box>

      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <TabPanel value={currentTab} index={0}>
          {renderUsersTab()}
        </TabPanel>
        <TabPanel value={currentTab} index={1}>
          {renderCommentsTab()}
        </TabPanel>
        <TabPanel value={currentTab} index={2}>
          {renderActivityTab()}
        </TabPanel>
        <TabPanel value={currentTab} index={3}>
          {renderNotificationsTab()}
        </TabPanel>
      </Box>

      {/* Comment actions menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          const comment = comments.find(c => c.id === selectedComment);
          if (comment) startEdit(comment);
        }}>
          <EditIcon sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={() => {
          if (selectedComment) handleDeleteComment(selectedComment);
        }}>
          <DeleteIcon sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>
    </Paper>
  );
};