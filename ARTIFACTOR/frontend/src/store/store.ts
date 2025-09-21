import { configureStore } from '@reduxjs/toolkit';
import authSlice from './slices/authSlice';
import artifactsSlice from './slices/artifactsSlice';
import notificationsSlice from './slices/notificationsSlice';
import uiSlice from './slices/uiSlice';
import collaborationSlice from './slices/collaborationSlice';
import pluginsSlice from './slices/pluginsSlice';
import searchSlice from './slices/searchSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    artifacts: artifactsSlice,
    notifications: notificationsSlice,
    ui: uiSlice,
    collaboration: collaborationSlice,
    plugins: pluginsSlice,
    search: searchSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['websocket/connected', 'websocket/disconnected'],
        ignoredPaths: ['ui.websocket'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;