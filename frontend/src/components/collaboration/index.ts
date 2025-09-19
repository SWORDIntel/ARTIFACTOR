/**
 * Collaboration components and hooks export for ARTIFACTOR v3.0
 */

export { CollaborationProvider, useCollaboration } from './CollaborationProvider';
export { CollaborationSidebar } from './CollaborationSidebar';
export { PresenceIndicator } from './PresenceIndicator';
export {
  useCollaborativeEditor,
  useComments,
  usePresence,
  useNotifications,
  useActivityFeed,
  useCollaborationMetrics,
  useCollaborationStatus
} from './CollaborationHooks';

// Type exports
export type {
  User,
  ActiveUser,
  Comment,
  Activity,
  Notification
} from './CollaborationProvider';