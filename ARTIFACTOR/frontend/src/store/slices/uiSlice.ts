import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ViewType } from '../../types';

interface UIState {
  theme: 'dark'; // User hates light themes!
  sidebarOpen: boolean;
  currentView: ViewType;
  isLoading: boolean;
  selectedArtifacts: string[];
  searchQuery: string;
  websocket: WebSocket | null;
  onlineUsers: string[];
  notifications: {
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'warning' | 'info';
  };
}

const initialState: UIState = {
  theme: 'dark', // ALWAYS dark - user hates light themes!
  sidebarOpen: true,
  currentView: ViewType.GRID,
  isLoading: false,
  selectedArtifacts: [],
  searchQuery: '',
  websocket: null,
  onlineUsers: [],
  notifications: {
    open: false,
    message: '',
    severity: 'info',
  },
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Theme is ALWAYS dark - user hates light themes!
    // No theme toggle functionality included
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    setCurrentView: (state, action: PayloadAction<ViewType>) => {
      state.currentView = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setSelectedArtifacts: (state, action: PayloadAction<string[]>) => {
      state.selectedArtifacts = action.payload;
    },
    toggleArtifactSelection: (state, action: PayloadAction<string>) => {
      const artifactId = action.payload;
      const index = state.selectedArtifacts.indexOf(artifactId);
      if (index === -1) {
        state.selectedArtifacts.push(artifactId);
      } else {
        state.selectedArtifacts.splice(index, 1);
      }
    },
    clearSelection: (state) => {
      state.selectedArtifacts = [];
    },
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    setWebSocket: (state, action: PayloadAction<WebSocket | null>) => {
      state.websocket = action.payload;
    },
    setOnlineUsers: (state, action: PayloadAction<string[]>) => {
      state.onlineUsers = action.payload;
    },
    addOnlineUser: (state, action: PayloadAction<string>) => {
      if (!state.onlineUsers.includes(action.payload)) {
        state.onlineUsers.push(action.payload);
      }
    },
    removeOnlineUser: (state, action: PayloadAction<string>) => {
      state.onlineUsers = state.onlineUsers.filter(userId => userId !== action.payload);
    },
    showNotification: (state, action: PayloadAction<{
      message: string;
      severity: 'success' | 'error' | 'warning' | 'info';
    }>) => {
      state.notifications = {
        open: true,
        message: action.payload.message,
        severity: action.payload.severity,
      };
    },
    hideNotification: (state) => {
      state.notifications.open = false;
    },
    resetUI: (state) => {
      return {
        ...initialState,
        theme: 'dark', // Always reset to dark theme!
      };
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  setCurrentView,
  setLoading,
  setSelectedArtifacts,
  toggleArtifactSelection,
  clearSelection,
  setSearchQuery,
  setWebSocket,
  setOnlineUsers,
  addOnlineUser,
  removeOnlineUser,
  showNotification,
  hideNotification,
  resetUI,
} = uiSlice.actions;

export default uiSlice.reducer;