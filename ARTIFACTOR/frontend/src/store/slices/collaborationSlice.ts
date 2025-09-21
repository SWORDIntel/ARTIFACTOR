import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Collaborator, Comment } from '../../types';

interface CollaborationState {
  activeCollaborators: Collaborator[];
  comments: Comment[];
  currentTypingUsers: string[];
  cursors: { [userId: string]: { line: number; column: number } };
  isConnected: boolean;
}

const initialState: CollaborationState = {
  activeCollaborators: [],
  comments: [],
  currentTypingUsers: [],
  cursors: {},
  isConnected: false,
};

const collaborationSlice = createSlice({
  name: 'collaboration',
  initialState,
  reducers: {
    setConnected: (state, action: PayloadAction<boolean>) => {
      state.isConnected = action.payload;
    },
    setCollaborators: (state, action: PayloadAction<Collaborator[]>) => {
      state.activeCollaborators = action.payload;
    },
    addCollaborator: (state, action: PayloadAction<Collaborator>) => {
      const existing = state.activeCollaborators.find(c => c.userId === action.payload.userId);
      if (!existing) {
        state.activeCollaborators.push(action.payload);
      }
    },
    removeCollaborator: (state, action: PayloadAction<string>) => {
      state.activeCollaborators = state.activeCollaborators.filter(c => c.userId !== action.payload);
    },
    updateCollaboratorStatus: (state, action: PayloadAction<{ userId: string; isOnline: boolean }>) => {
      const collaborator = state.activeCollaborators.find(c => c.userId === action.payload.userId);
      if (collaborator) {
        collaborator.isOnline = action.payload.isOnline;
        collaborator.lastActive = new Date();
      }
    },
    addComment: (state, action: PayloadAction<Comment>) => {
      state.comments.push(action.payload);
    },
    updateComment: (state, action: PayloadAction<Comment>) => {
      const index = state.comments.findIndex(c => c.id === action.payload.id);
      if (index !== -1) {
        state.comments[index] = action.payload;
      }
    },
    deleteComment: (state, action: PayloadAction<string>) => {
      state.comments = state.comments.filter(c => c.id !== action.payload);
    },
    setComments: (state, action: PayloadAction<Comment[]>) => {
      state.comments = action.payload;
    },
    addTypingUser: (state, action: PayloadAction<string>) => {
      if (!state.currentTypingUsers.includes(action.payload)) {
        state.currentTypingUsers.push(action.payload);
      }
    },
    removeTypingUser: (state, action: PayloadAction<string>) => {
      state.currentTypingUsers = state.currentTypingUsers.filter(u => u !== action.payload);
    },
    updateCursor: (state, action: PayloadAction<{ userId: string; line: number; column: number }>) => {
      state.cursors[action.payload.userId] = {
        line: action.payload.line,
        column: action.payload.column,
      };
    },
    removeCursor: (state, action: PayloadAction<string>) => {
      delete state.cursors[action.payload];
    },
  },
});

export const {
  setConnected,
  setCollaborators,
  addCollaborator,
  removeCollaborator,
  updateCollaboratorStatus,
  addComment,
  updateComment,
  deleteComment,
  setComments,
  addTypingUser,
  removeTypingUser,
  updateCursor,
  removeCursor,
} = collaborationSlice.actions;

export default collaborationSlice.reducer;