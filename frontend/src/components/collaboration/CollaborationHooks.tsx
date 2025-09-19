/**
 * Custom hooks for collaboration features in ARTIFACTOR v3.0
 * Provides reusable collaboration functionality
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useCollaboration } from './CollaborationProvider';
import { debounce } from 'lodash';

/**
 * Hook for handling real-time text editing with collaboration
 */
export const useCollaborativeEditor = () => {
  const {
    updateCursorPosition,
    updateSelection,
    startTyping,
    stopTyping,
    sendArtifactEdit,
    isConnected
  } = useCollaboration();

  const [isTyping, setIsTyping] = useState(false);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Debounced cursor position update
  const debouncedCursorUpdate = useCallback(
    debounce((line: number, column: number) => {
      if (isConnected) {
        updateCursorPosition(line, column);
      }
    }, 100),
    [updateCursorPosition, isConnected]
  );

  // Handle cursor position changes
  const handleCursorChange = useCallback((line: number, column: number) => {
    debouncedCursorUpdate(line, column);
  }, [debouncedCursorUpdate]);

  // Handle text selection changes
  const handleSelectionChange = useCallback((
    start: { line: number; column: number },
    end: { line: number; column: number }
  ) => {
    if (isConnected) {
      updateSelection(start, end);
    }
  }, [updateSelection, isConnected]);

  // Handle typing events
  const handleTextChange = useCallback((content: string, changeData?: any) => {
    if (!isConnected) return;

    // Start typing indicator if not already typing
    if (!isTyping) {
      setIsTyping(true);
      startTyping();
    }

    // Reset typing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Send edit data
    sendArtifactEdit({
      type: 'text_change',
      content,
      changeData,
      timestamp: Date.now()
    });

    // Stop typing after 2 seconds of inactivity
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
      stopTyping();
    }, 2000);
  }, [isConnected, isTyping, startTyping, stopTyping, sendArtifactEdit]);

  // Cleanup typing timeout on unmount
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  return {
    handleCursorChange,
    handleSelectionChange,
    handleTextChange,
    isTyping,
    isConnected
  };
};

/**
 * Hook for managing comment interactions
 */
export const useComments = () => {
  const {
    comments,
    addComment,
    updateComment,
    deleteComment,
    loadComments
  } = useCollaboration();

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddComment = useCallback(async (
    content: string,
    parentId?: string,
    positionData?: any,
    mentions?: string[]
  ) => {
    setIsLoading(true);
    setError(null);

    try {
      await addComment(content, parentId, positionData, mentions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add comment');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [addComment]);

  const handleUpdateComment = useCallback(async (commentId: string, content: string) => {
    setIsLoading(true);
    setError(null);

    try {
      await updateComment(commentId, content);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update comment');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [updateComment]);

  const handleDeleteComment = useCallback(async (commentId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      await deleteComment(commentId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete comment');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [deleteComment]);

  // Group comments by thread
  const commentThreads = useCallback(() => {
    const topLevelComments = comments.filter(comment => !comment.parent_id);
    return topLevelComments.map(comment => ({
      ...comment,
      replies: comments.filter(reply => reply.parent_id === comment.id)
    }));
  }, [comments]);

  return {
    comments,
    commentThreads: commentThreads(),
    isLoading,
    error,
    addComment: handleAddComment,
    updateComment: handleUpdateComment,
    deleteComment: handleDeleteComment,
    loadComments
  };
};

/**
 * Hook for presence awareness
 */
export const usePresence = () => {
  const { activeUsers, currentUser, typingUsers } = useCollaboration();

  // Get users currently active in the artifact
  const getActiveUsers = useCallback(() => {
    return activeUsers.filter(user => user.user_id !== currentUser?.id);
  }, [activeUsers, currentUser]);

  // Get users currently typing
  const getTypingUsers = useCallback(() => {
    return activeUsers.filter(user =>
      typingUsers.includes(user.user_id) && user.user_id !== currentUser?.id
    );
  }, [activeUsers, typingUsers, currentUser]);

  // Check if a specific user is active
  const isUserActive = useCallback((userId: string) => {
    return activeUsers.some(user => user.user_id === userId && user.status === 'active');
  }, [activeUsers]);

  // Get cursor position for a user
  const getUserCursor = useCallback((userId: string) => {
    const user = activeUsers.find(u => u.user_id === userId);
    return user?.cursor;
  }, [activeUsers]);

  // Get selection for a user
  const getUserSelection = useCallback((userId: string) => {
    const user = activeUsers.find(u => u.user_id === userId);
    return user?.selection;
  }, [activeUsers]);

  return {
    activeUsers: getActiveUsers(),
    typingUsers: getTypingUsers(),
    isUserActive,
    getUserCursor,
    getUserSelection,
    totalActiveUsers: activeUsers.length
  };
};

/**
 * Hook for notification management
 */
export const useNotifications = () => {
  const {
    notifications,
    notificationCounts,
    markNotificationRead,
    markAllNotificationsRead,
    loadNotifications
  } = useCollaboration();

  const [isLoading, setIsLoading] = useState(false);

  // Get unread notifications
  const unreadNotifications = useCallback(() => {
    return notifications.filter(notification => !notification.read);
  }, [notifications]);

  // Get high priority notifications
  const urgentNotifications = useCallback(() => {
    return notifications.filter(notification =>
      !notification.read && (notification.priority === 'high' || notification.priority === 'urgent')
    );
  }, [notifications]);

  // Mark notification as read with error handling
  const handleMarkRead = useCallback(async (notificationId: string) => {
    setIsLoading(true);
    try {
      await markNotificationRead(notificationId);
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    } finally {
      setIsLoading(false);
    }
  }, [markNotificationRead]);

  // Mark all notifications as read with error handling
  const handleMarkAllRead = useCallback(async () => {
    setIsLoading(true);
    try {
      await markAllNotificationsRead();
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err);
    } finally {
      setIsLoading(false);
    }
  }, [markAllNotificationsRead]);

  return {
    notifications,
    unreadNotifications: unreadNotifications(),
    urgentNotifications: urgentNotifications(),
    notificationCounts,
    isLoading,
    markAsRead: handleMarkRead,
    markAllAsRead: handleMarkAllRead,
    loadNotifications
  };
};

/**
 * Hook for activity feed management
 */
export const useActivityFeed = () => {
  const { activities, loadActivities } = useCollaboration();

  // Group activities by date
  const groupedActivities = useCallback(() => {
    const groups: Record<string, typeof activities> = {};

    activities.forEach(activity => {
      const date = new Date(activity.timestamp).toDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(activity);
    });

    return Object.entries(groups).sort(([a], [b]) =>
      new Date(b).getTime() - new Date(a).getTime()
    );
  }, [activities]);

  // Filter activities by type
  const getActivitiesByType = useCallback((type: string) => {
    return activities.filter(activity => activity.activity_type === type);
  }, [activities]);

  // Filter activities by category
  const getActivitiesByCategory = useCallback((category: string) => {
    return activities.filter(activity => activity.activity_category === category);
  }, [activities]);

  return {
    activities,
    groupedActivities: groupedActivities(),
    getActivitiesByType,
    getActivitiesByCategory,
    loadActivities
  };
};

/**
 * Hook for collaboration metrics and analytics
 */
export const useCollaborationMetrics = () => {
  const { activeUsers, comments, activities, notifications } = useCollaboration();

  // Calculate collaboration statistics
  const metrics = useCallback(() => {
    const totalUsers = activeUsers.length;
    const totalComments = comments.length;
    const totalActivities = activities.length;
    const unreadNotifications = notifications.filter(n => !n.read).length;

    // Comment engagement metrics
    const threadsWithReplies = comments
      .filter(c => !c.parent_id)
      .filter(c => comments.some(reply => reply.parent_id === c.id));

    const engagementRate = comments.length > 0
      ? (threadsWithReplies.length / comments.filter(c => !c.parent_id).length) * 100
      : 0;

    return {
      totalUsers,
      totalComments,
      totalActivities,
      unreadNotifications,
      engagementRate: Math.round(engagementRate),
      threadsWithReplies: threadsWithReplies.length
    };
  }, [activeUsers, comments, activities, notifications]);

  return metrics();
};

/**
 * Hook for connection status and error handling
 */
export const useCollaborationStatus = () => {
  const { isConnected, connectionError } = useCollaboration();
  const [retryCount, setRetryCount] = useState(0);
  const [lastError, setLastError] = useState<string | null>(null);

  useEffect(() => {
    if (connectionError) {
      setLastError(connectionError);
      setRetryCount(prev => prev + 1);
    } else if (isConnected) {
      setRetryCount(0);
      setLastError(null);
    }
  }, [isConnected, connectionError]);

  const shouldShowError = !isConnected && retryCount > 2;

  return {
    isConnected,
    connectionError: lastError,
    retryCount,
    shouldShowError,
    isRetrying: !isConnected && retryCount > 0 && retryCount <= 2
  };
};