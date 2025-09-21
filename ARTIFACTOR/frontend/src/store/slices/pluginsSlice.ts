import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Plugin } from '../../types';
import * as pluginService from '../../services/pluginService';

interface PluginsState {
  plugins: Plugin[];
  installedPlugins: Plugin[];
  isLoading: boolean;
  error: string | null;
}

const initialState: PluginsState = {
  plugins: [],
  installedPlugins: [],
  isLoading: false,
  error: null,
};

export const fetchPlugins = createAsyncThunk(
  'plugins/fetchPlugins',
  async (_, { rejectWithValue }) => {
    try {
      const response = await pluginService.getPlugins();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch plugins');
    }
  }
);

export const installPlugin = createAsyncThunk(
  'plugins/installPlugin',
  async (pluginId: string, { rejectWithValue }) => {
    try {
      const response = await pluginService.installPlugin(pluginId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to install plugin');
    }
  }
);

const pluginsSlice = createSlice({
  name: 'plugins',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPlugins.fulfilled, (state, action) => {
        state.plugins = action.payload;
        state.installedPlugins = action.payload.filter((p: Plugin) => p.isInstalled);
      })
      .addCase(installPlugin.fulfilled, (state, action) => {
        const plugin = action.payload;
        const index = state.plugins.findIndex(p => p.id === plugin.id);
        if (index !== -1) {
          state.plugins[index] = plugin;
        }
        if (plugin.isInstalled && !state.installedPlugins.find(p => p.id === plugin.id)) {
          state.installedPlugins.push(plugin);
        }
      });
  },
});

export const { clearError } = pluginsSlice.actions;
export default pluginsSlice.reducer;