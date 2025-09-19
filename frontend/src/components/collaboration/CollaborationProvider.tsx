/**
 * Collaboration context provider for ARTIFACTOR v3.0
 * Manages real-time collaboration state, WebSocket connections, and notifications
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuth } from '../auth/AuthContext';

export interface User {
  id: string;
  username: string;
  email: string;
  display_name?: string;
}

export interface ActiveUser {
  user_id: string;
  user_data: User;
  cursor?: {
    line: number;
    column: number;
  };
  selection?: {
    start: { line: number; column: number };
    end: { line: number; column: number };
  };
  activity?: string;
  status: 'active' | 'away' | 'offline';
}

export interface Comment {
  id: string;
  content: string;
  content_type: string;
  parent_id?: string;
  position_data?: any;
  mentions: string[];
  reactions: Record<string, string[]>;
  created_at: string;
  updated_at: string;
  edited: boolean;
  resolved: boolean;
  resolved_at?: string;
  user: User;
  replies?: Comment[];
}

export interface Activity {
  id: string;
  activity_type: string;
  activity_category: string;
  description: string;
  data: any;
  timestamp: string;
  visibility: string;
  tags: string[];
  user: User;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  artifact_id?: string;
  related_user_id?: string;
  related_comment_id?: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  read: boolean;
  read_at?: string;
  created_at: string;
  data: any;
}

interface CollaborationContextType {
  // Connection state
  isConnected: boolean;
  connectionError?: string;

  // Users and presence
  activeUsers: ActiveUser[];
  currentUser?: User;
  typingUsers: string[];

  // Comments
  comments: Comment[];
  addComment: (content: string, parentId?: string, positionData?: any, mentions?: string[]) => Promise<void>;
  updateComment: (commentId: string, content: string) => Promise<void>;
  deleteComment: (commentId: string) => Promise<void>;
  loadComments: (parentId?: string) => Promise<void>;

  // Activities
  activities: Activity[];
  loadActivities: () => Promise<void>;

  // Notifications
  notifications: Notification[];
  notificationCounts: { total: number; unread: number; urgent: number };
  markNotificationRead: (notificationId: string) => Promise<void>;
  markAllNotificationsRead: () => Promise<void>;
  loadNotifications: () => Promise<void>;

  // Real-time collaboration
  updateCursorPosition: (line: number, column: number) => void;
  updateSelection: (start: { line: number; column: number }, end: { line: number; column: number }) => void;
  startTyping: () => void;
  stopTyping: () => void;
  sendArtifactEdit: (editData: any) => void;

  // Utility functions
  connect: (artifactId: string) => void;
  disconnect: () => void;
}

const CollaborationContext = createContext<CollaborationContextType | undefined>(undefined);

interface CollaborationProviderProps {
  children: React.ReactNode;
  artifactId: string;
}

export const CollaborationProvider: React.FC<CollaborationProviderProps> = ({
  children,
  artifactId
}) => {
  const { user: authUser, token } = useAuth();
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | undefined>();

  // State
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [notificationCounts, setNotificationCounts] = useState({
    total: 0,
    unread: 0,
    urgent: 0
  });

  // Refs for debouncing
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const cursorUpdateTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback((artifactId: string) => {
    if (!authUser || !token) return;

    const newSocket = io(`ws://localhost:8000/api/collaboration/ws/${artifactId}`, {
      query: { token },
      transports: ['websocket']
    });

    newSocket.on('connect', () => {
      setIsConnected(true);
      setConnectionError(undefined);
      console.log('Connected to collaboration socket');
    });

    newSocket.on('disconnect', () => {
      setIsConnected(false);
      console.log('Disconnected from collaboration socket');
    });

    newSocket.on('connect_error', (error) => {
      setConnectionError(error.message);
      console.error('WebSocket connection error:', error);
    });

    // Handle room state (initial state when joining)
    newSocket.on('room_state', (data) => {
      setActiveUsers(data.data.active_users || []);
      setTypingUsers(data.data.typing_users || []);
    });

    // Handle user join/leave
    newSocket.on('user_join', (data) => {
      setActiveUsers(prev => [
        ...prev.filter(u => u.user_id !== data.user_id),
        {
          user_id: data.user_id,
          user_data: data.user_data,
          status: 'active'
        }
      ]);
    });

    newSocket.on('user_leave', (data) => {
      setActiveUsers(prev => prev.filter(u => u.user_id !== data.user_id));
      setTypingUsers(prev => prev.filter(id => id !== data.user_id));
    });

    // Handle presence updates
    newSocket.on('cursor_move', (data) => {
      setActiveUsers(prev => prev.map(user =>
        user.user_id === data.user_id
          ? { ...user, cursor: data.data }
          : user
      ));
    });

    newSocket.on('selection_change', (data) => {
      setActiveUsers(prev => prev.map(user =>
        user.user_id === data.user_id
          ? { ...user, selection: data.data }
          : user
      ));
    });

    // Handle typing indicators
    newSocket.on('typing_start', (data) => {
      setTypingUsers(prev => [...new Set([...prev, data.user_id])]);
    });

    newSocket.on('typing_stop', (data) => {
      setTypingUsers(prev => prev.filter(id => id !== data.user_id));
    });

    // Handle comments
    newSocket.on('comment_add', (data) => {
      const newComment: Comment = {
        id: data.data.comment_id,
        content: data.data.content,
        content_type: 'text',
        parent_id: data.data.parent_id,
        position_data: data.data.position_data,
        mentions: data.data.mentions || [],
        reactions: {},
        created_at: data.timestamp,
        updated_at: data.timestamp,
        edited: false,
        resolved: false,
        user: data.data.user
      };

      setComments(prev => [newComment, ...prev]);
    });

    newSocket.on('comment_update', (data) => {
      setComments(prev => prev.map(comment =>
        comment.id === data.data.comment_id
          ? {
              ...comment,
              content: data.data.content,
              content_type: data.data.content_type,
              edited: data.data.edited,
              updated_at: data.timestamp
            }
          : comment
      ));
    });

    newSocket.on('comment_delete', (data) => {
      setComments(prev => prev.filter(comment => comment.id !== data.data.comment_id));
    });

    // Handle notifications
    newSocket.on('notification', (data) => {
      setNotifications(prev => [data.data, ...prev]);
      setNotificationCounts(prev => ({
        total: prev.total + 1,
        unread: prev.unread + 1,
        urgent: prev.urgent + (data.data.priority === 'high' || data.data.priority === 'urgent' ? 1 : 0)
      }));
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, [authUser, token]);

  const disconnect = useCallback(() => {
    if (socket) {
      socket.disconnect();
      setSocket(null);
    }
    setIsConnected(false);
    setActiveUsers([]);
    setTypingUsers([]);
  }, [socket]);

  // Connect when component mounts or artifactId changes
  useEffect(() => {
    if (artifactId) {
      connect(artifactId);
    }

    return () => {
      disconnect();
    };
  }, [artifactId, connect, disconnect]);

  // Real-time collaboration functions
  const updateCursorPosition = useCallback((line: number, column: number) => {
    if (!socket || !isConnected) return;

    // Debounce cursor updates
    if (cursorUpdateTimeoutRef.current) {
      clearTimeout(cursorUpdateTimeoutRef.current);
    }

    cursorUpdateTimeoutRef.current = setTimeout(() => {
      socket.emit('message', JSON.stringify({
        type: 'cursor_move',
        data: { line, column }
      }));
    }, 100);
  }, [socket, isConnected]);

  const updateSelection = useCallback((
    start: { line: number; column: number },
    end: { line: number; column: number }
  ) => {
    if (!socket || !isConnected) return;

    socket.emit('message', JSON.stringify({
      type: 'selection_change',
      data: { start, end }
    }));
  }, [socket, isConnected]);

  const startTyping = useCallback(() => {
    if (!socket || !isConnected) return;

    socket.emit('message', JSON.stringify({
      type: 'typing_start'
    }));

    // Auto-stop typing after 3 seconds
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    typingTimeoutRef.current = setTimeout(() => {
      stopTyping();
    }, 3000);
  }, [socket, isConnected]);

  const stopTyping = useCallback(() => {
    if (!socket || !isConnected) return;

    socket.emit('message', JSON.stringify({
      type: 'typing_stop'
    }));

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = null;
    }
  }, [socket, isConnected]);

  const sendArtifactEdit = useCallback((editData: any) => {
    if (!socket || !isConnected) return;

    socket.emit('message', JSON.stringify({
      type: 'artifact_edit',
      data: editData
    }));
  }, [socket, isConnected]);

  // Comment functions
  const addComment = useCallback(async (
    content: string,
    parentId?: string,
    positionData?: any,
    mentions?: string[]
  ) => {
    try {
      const response = await fetch(`/api/collaboration/artifacts/${artifactId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          content,
          parent_id: parentId,
          position_data: positionData,
          mentions: mentions || []
        })
      });

      if (!response.ok) {
        throw new Error('Failed to add comment');
      }

      // Comment will be added via WebSocket event
    } catch (error) {
      console.error('Error adding comment:', error);
      throw error;
    }
  }, [artifactId, token]);

  const updateComment = useCallback(async (commentId: string, content: string) => {
    try {
      const response = await fetch(`/api/collaboration/artifacts/${artifactId}/comments/${commentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          content,
          content_type: 'text'
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update comment');
      }

      // Comment will be updated via WebSocket event
    } catch (error) {
      console.error('Error updating comment:', error);
      throw error;
    }
  }, [artifactId, token]);

  const deleteComment = useCallback(async (commentId: string) => {
    try {
      const response = await fetch(`/api/collaboration/artifacts/${artifactId}/comments/${commentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete comment');
      }

      // Comment will be removed via WebSocket event
    } catch (error) {
      console.error('Error deleting comment:', error);
      throw error;
    }
  }, [artifactId, token]);

  const loadComments = useCallback(async (parentId?: string) => {
    try {
      const url = new URL(`/api/collaboration/artifacts/${artifactId}/comments`, window.location.origin);
      if (parentId) {
        url.searchParams.set('parent_id', parentId);
      }

      const response = await fetch(url.toString(), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load comments');
      }

      const data = await response.json();
      setComments(data.comments);
    } catch (error) {
      console.error('Error loading comments:', error);
    }
  }, [artifactId, token]);

  // Activity functions
  const loadActivities = useCallback(async () => {
    try {
      const response = await fetch(`/api/collaboration/artifacts/${artifactId}/activity`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load activities');
      }

      const data = await response.json();
      setActivities(data.activities);
    } catch (error) {
      console.error('Error loading activities:', error);
    }
  }, [artifactId, token]);

  // Notification functions
  const loadNotifications = useCallback(async () => {
    try {
      const [notificationsResponse, countsResponse] = await Promise.all([
        fetch('/api/collaboration/notifications', {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch('/api/collaboration/notifications/counts', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (notificationsResponse.ok) {
        const notificationsData = await notificationsResponse.json();
        setNotifications(notificationsData.notifications);
      }

      if (countsResponse.ok) {
        const countsData = await countsResponse.json();
        setNotificationCounts(countsData);
      }
    } catch (error) {
      console.error('Error loading notifications:', error);
    }
  }, [token]);

  const markNotificationRead = useCallback(async (notificationId: string) => {
    try {
      const response = await fetch('/api/collaboration/notifications/mark-read', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          notification_ids: [notificationId]
        })
      });

      if (response.ok) {
        setNotifications(prev => prev.map(notification =>
          notification.id === notificationId
            ? { ...notification, read: true, read_at: new Date().toISOString() }
            : notification
        ));
        setNotificationCounts(prev => ({
          ...prev,
          unread: Math.max(0, prev.unread - 1)
        }));
      }
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  }, [token]);

  const markAllNotificationsRead = useCallback(async () => {
    try {
      const response = await fetch('/api/collaboration/notifications/mark-all-read', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setNotifications(prev => prev.map(notification => ({
          ...notification,
          read: true,
          read_at: new Date().toISOString()
        })));
        setNotificationCounts(prev => ({
          ...prev,
          unread: 0,
          urgent: 0
        }));
      }
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  }, [token]);

  // Load initial data
  useEffect(() => {
    if (artifactId && token) {
      loadComments();
      loadActivities();
      loadNotifications();
    }
  }, [artifactId, token, loadComments, loadActivities, loadNotifications]);

  const contextValue: CollaborationContextType = {
    // Connection state
    isConnected,
    connectionError,

    // Users and presence
    activeUsers,
    currentUser: authUser,
    typingUsers,

    // Comments
    comments,
    addComment,
    updateComment,
    deleteComment,
    loadComments,

    // Activities
    activities,
    loadActivities,

    // Notifications
    notifications,
    notificationCounts,
    markNotificationRead,
    markAllNotificationsRead,
    loadNotifications,

    // Real-time collaboration
    updateCursorPosition,
    updateSelection,
    startTyping,
    stopTyping,
    sendArtifactEdit,

    // Utility functions
    connect,
    disconnect
  };

  return (
    <CollaborationContext.Provider value={contextValue}>
      {children}
    </CollaborationContext.Provider>
  );
};

export const useCollaboration = () => {
  const context = useContext(CollaborationContext);
  if (context === undefined) {
    throw new Error('useCollaboration must be used within a CollaborationProvider');
  }
  return context;
};