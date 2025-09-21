// ARTIFACTOR v3.0 TypeScript Type Definitions
// Beautiful dark theme enterprise artifact management platform

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: UserRole;
  preferences: UserPreferences;
  createdAt: Date;
  lastLogin: Date;
}

export enum UserRole {
  ADMIN = 'admin',
  MODERATOR = 'moderator',
  USER = 'user',
  VIEWER = 'viewer',
}

export interface UserPreferences {
  notifications: boolean;
  autoSave: boolean;
  defaultView: ViewType;
  itemsPerPage: number;
}

export interface Artifact {
  id: string;
  title: string;
  description: string;
  content: string;
  type: ArtifactType;
  category: string;
  tags: string[];
  metadata: ArtifactMetadata;
  classification: MLClassification;
  collaborators: Collaborator[];
  isPublic: boolean;
  isArchived: boolean;
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
  version: number;
  fileSize: number;
  hash: string;
}

export enum ArtifactType {
  CODE = 'code',
  DOCUMENTATION = 'documentation',
  DESIGN = 'design',
  DATA = 'data',
  PRESENTATION = 'presentation',
  OTHER = 'other',
}

export interface ArtifactMetadata {
  language?: string;
  framework?: string;
  dependencies?: string[];
  license?: string;
  difficulty: DifficultyLevel;
  estimatedTime?: number;
  sourceUrl?: string;
  originalConversationId?: string;
}

export enum DifficultyLevel {
  BEGINNER = 'beginner',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced',
  EXPERT = 'expert',
}

export interface MLClassification {
  primaryCategory: string;
  confidence: number;
  categories: CategoryScore[];
  keywords: string[];
  sentiment: SentimentAnalysis;
  complexity: ComplexityAnalysis;
  lastClassified: Date;
}

export interface CategoryScore {
  category: string;
  score: number;
}

export interface SentimentAnalysis {
  positive: number;
  neutral: number;
  negative: number;
  overall: 'positive' | 'neutral' | 'negative';
}

export interface ComplexityAnalysis {
  linesOfCode?: number;
  cyclomaticComplexity?: number;
  maintainabilityIndex?: number;
  techDebt?: number;
  score: number;
  level: 'low' | 'medium' | 'high' | 'very_high';
}

export interface Collaborator {
  userId: string;
  userName: string;
  userAvatar?: string;
  role: CollaborationRole;
  permissions: Permission[];
  joinedAt: Date;
  lastActive: Date;
  isOnline: boolean;
}

export enum CollaborationRole {
  OWNER = 'owner',
  EDITOR = 'editor',
  VIEWER = 'viewer',
  COMMENTER = 'commenter',
}

export enum Permission {
  READ = 'read',
  WRITE = 'write',
  DELETE = 'delete',
  SHARE = 'share',
  COMMENT = 'comment',
  MODERATE = 'moderate',
}

export interface Comment {
  id: string;
  artifactId: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  content: string;
  parentId?: string;
  replies: Comment[];
  reactions: Reaction[];
  isEdited: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface Reaction {
  id: string;
  userId: string;
  userName: string;
  type: ReactionType;
  createdAt: Date;
}

export enum ReactionType {
  LIKE = 'like',
  LOVE = 'love',
  LAUGH = 'laugh',
  ANGRY = 'angry',
  SAD = 'sad',
  THUMBS_UP = 'thumbs_up',
  THUMBS_DOWN = 'thumbs_down',
}

export interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  authorAvatar?: string;
  icon?: string;
  screenshots: string[];
  category: PluginCategory;
  tags: string[];
  price: number;
  rating: PluginRating;
  downloads: number;
  isInstalled: boolean;
  isEnabled: boolean;
  permissions: Permission[];
  dependencies: PluginDependency[];
  compatibility: string[];
  size: number;
  lastUpdated: Date;
  publishedAt: Date;
}

export enum PluginCategory {
  UTILITY = 'utility',
  INTEGRATION = 'integration',
  VISUALIZATION = 'visualization',
  ANALYSIS = 'analysis',
  AUTOMATION = 'automation',
  SECURITY = 'security',
  PERFORMANCE = 'performance',
  UI_UX = 'ui_ux',
}

export interface PluginRating {
  average: number;
  total: number;
  distribution: RatingDistribution;
}

export interface RatingDistribution {
  five: number;
  four: number;
  three: number;
  two: number;
  one: number;
}

export interface PluginDependency {
  id: string;
  name: string;
  version: string;
  required: boolean;
}

export interface SearchQuery {
  query: string;
  filters: SearchFilters;
  sort: SortOption;
  page: number;
  limit: number;
}

export interface SearchFilters {
  type?: ArtifactType[];
  category?: string[];
  tags?: string[];
  difficulty?: DifficultyLevel[];
  dateRange?: DateRange;
  createdBy?: string[];
  collaborators?: string[];
  isPublic?: boolean;
  hasComments?: boolean;
  minRating?: number;
}

export interface DateRange {
  from: Date;
  to: Date;
}

export interface SortOption {
  field: SortField;
  direction: SortDirection;
}

export enum SortField {
  RELEVANCE = 'relevance',
  CREATED_AT = 'createdAt',
  UPDATED_AT = 'updatedAt',
  TITLE = 'title',
  RATING = 'rating',
  VIEWS = 'views',
  COMMENTS = 'comments',
  FILE_SIZE = 'fileSize',
}

export enum SortDirection {
  ASC = 'asc',
  DESC = 'desc',
}

export interface SearchResult {
  artifacts: Artifact[];
  total: number;
  page: number;
  pages: number;
  hasNext: boolean;
  hasPrevious: boolean;
  searchTime: number;
  suggestions: string[];
}

export interface Notification {
  id: string;
  userId: string;
  title: string;
  message: string;
  type: NotificationType;
  category: NotificationCategory;
  data?: any;
  isRead: boolean;
  isActionable: boolean;
  actions?: NotificationAction[];
  createdAt: Date;
  expiresAt?: Date;
}

export enum NotificationType {
  INFO = 'info',
  SUCCESS = 'success',
  WARNING = 'warning',
  ERROR = 'error',
}

export enum NotificationCategory {
  SYSTEM = 'system',
  COLLABORATION = 'collaboration',
  SECURITY = 'security',
  UPDATE = 'update',
  REMINDER = 'reminder',
  ACHIEVEMENT = 'achievement',
}

export interface NotificationAction {
  id: string;
  label: string;
  action: string;
  style: 'primary' | 'secondary' | 'danger';
}

export interface WebSocketMessage {
  type: WebSocketMessageType;
  payload: any;
  timestamp: Date;
  userId?: string;
  artifactId?: string;
}

export enum WebSocketMessageType {
  USER_JOINED = 'user_joined',
  USER_LEFT = 'user_left',
  ARTIFACT_UPDATED = 'artifact_updated',
  COMMENT_ADDED = 'comment_added',
  COMMENT_UPDATED = 'comment_updated',
  COMMENT_DELETED = 'comment_deleted',
  TYPING_START = 'typing_start',
  TYPING_STOP = 'typing_stop',
  CURSOR_MOVED = 'cursor_moved',
  SELECTION_CHANGED = 'selection_changed',
  NOTIFICATION = 'notification',
}

export enum ViewType {
  GRID = 'grid',
  LIST = 'list',
  TABLE = 'table',
  KANBAN = 'kanban',
}

export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  metadata?: {
    page?: number;
    pages?: number;
    total?: number;
    limit?: number;
  };
}

export interface PaginationParams {
  page: number;
  limit: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

export interface FilterState {
  search: string;
  type: ArtifactType | 'all';
  category: string | 'all';
  difficulty: DifficultyLevel | 'all';
  dateRange: DateRange | null;
  isPublic: boolean | null;
  tags: string[];
}

export interface AppState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  artifacts: Artifact[];
  selectedArtifacts: string[];
  filters: FilterState;
  view: ViewType;
  notifications: Notification[];
  websocket: WebSocket | null;
  plugins: Plugin[];
  theme: 'dark'; // User hates light themes!
  sidebarOpen: boolean;
}

// Export utility types
export type Partial<T> = {
  [P in keyof T]?: T[P];
};

export type Pick<T, K extends keyof T> = {
  [P in K]: T[P];
};

export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};