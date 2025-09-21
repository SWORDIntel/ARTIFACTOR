import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Artifact, SearchQuery, SearchResult, FilterState, ViewType } from '../../types';
import * as artifactService from '../../services/artifactService';

interface ArtifactsState {
  artifacts: Artifact[];
  selectedArtifact: Artifact | null;
  searchResults: SearchResult | null;
  filters: FilterState;
  isLoading: boolean;
  error: string | null;
  currentPage: number;
  totalPages: number;
  totalItems: number;
}

const initialState: ArtifactsState = {
  artifacts: [],
  selectedArtifact: null,
  searchResults: null,
  filters: {
    search: '',
    type: 'all',
    category: 'all',
    difficulty: 'all',
    dateRange: null,
    isPublic: null,
    tags: [],
  },
  isLoading: false,
  error: null,
  currentPage: 1,
  totalPages: 1,
  totalItems: 0,
};

// Async thunks
export const fetchArtifacts = createAsyncThunk(
  'artifacts/fetchArtifacts',
  async ({ page = 1, limit = 20 }: { page?: number; limit?: number } = {}, { rejectWithValue }) => {
    try {
      const response = await artifactService.getArtifacts({ page, limit });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch artifacts');
    }
  }
);

export const searchArtifacts = createAsyncThunk(
  'artifacts/searchArtifacts',
  async (query: SearchQuery, { rejectWithValue }) => {
    try {
      const response = await artifactService.searchArtifacts(query);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Search failed');
    }
  }
);

export const getArtifactById = createAsyncThunk(
  'artifacts/getArtifactById',
  async (id: string, { rejectWithValue }) => {
    try {
      const response = await artifactService.getArtifactById(id);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch artifact');
    }
  }
);

export const createArtifact = createAsyncThunk(
  'artifacts/createArtifact',
  async (artifactData: Partial<Artifact>, { rejectWithValue }) => {
    try {
      const response = await artifactService.createArtifact(artifactData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to create artifact');
    }
  }
);

export const updateArtifact = createAsyncThunk(
  'artifacts/updateArtifact',
  async ({ id, data }: { id: string; data: Partial<Artifact> }, { rejectWithValue }) => {
    try {
      const response = await artifactService.updateArtifact(id, data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to update artifact');
    }
  }
);

export const deleteArtifact = createAsyncThunk(
  'artifacts/deleteArtifact',
  async (id: string, { rejectWithValue }) => {
    try {
      await artifactService.deleteArtifact(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to delete artifact');
    }
  }
);

export const bulkDeleteArtifacts = createAsyncThunk(
  'artifacts/bulkDeleteArtifacts',
  async (ids: string[], { rejectWithValue }) => {
    try {
      await artifactService.bulkDeleteArtifacts(ids);
      return ids;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to delete artifacts');
    }
  }
);

const artifactsSlice = createSlice({
  name: 'artifacts',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setFilters: (state, action: PayloadAction<Partial<FilterState>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = initialState.filters;
    },
    setSelectedArtifact: (state, action: PayloadAction<Artifact | null>) => {
      state.selectedArtifact = action.payload;
    },
    clearSearchResults: (state) => {
      state.searchResults = null;
    },
    setCurrentPage: (state, action: PayloadAction<number>) => {
      state.currentPage = action.payload;
    },
    // Optimistic update for real-time collaboration
    updateArtifactOptimistic: (state, action: PayloadAction<{ id: string; changes: Partial<Artifact> }>) => {
      const { id, changes } = action.payload;
      const index = state.artifacts.findIndex(artifact => artifact.id === id);
      if (index !== -1) {
        state.artifacts[index] = { ...state.artifacts[index], ...changes };
      }
      if (state.selectedArtifact?.id === id) {
        state.selectedArtifact = { ...state.selectedArtifact, ...changes };
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch artifacts
    builder
      .addCase(fetchArtifacts.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchArtifacts.fulfilled, (state, action) => {
        state.isLoading = false;
        state.artifacts = action.payload.artifacts;
        state.currentPage = action.payload.page;
        state.totalPages = action.payload.pages;
        state.totalItems = action.payload.total;
      })
      .addCase(fetchArtifacts.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Search artifacts
    builder
      .addCase(searchArtifacts.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(searchArtifacts.fulfilled, (state, action) => {
        state.isLoading = false;
        state.searchResults = action.payload;
      })
      .addCase(searchArtifacts.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Get artifact by ID
    builder
      .addCase(getArtifactById.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(getArtifactById.fulfilled, (state, action) => {
        state.isLoading = false;
        state.selectedArtifact = action.payload;
      })
      .addCase(getArtifactById.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Create artifact
    builder
      .addCase(createArtifact.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createArtifact.fulfilled, (state, action) => {
        state.isLoading = false;
        state.artifacts.unshift(action.payload);
        state.totalItems += 1;
      })
      .addCase(createArtifact.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Update artifact
    builder
      .addCase(updateArtifact.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateArtifact.fulfilled, (state, action) => {
        state.isLoading = false;
        const index = state.artifacts.findIndex(artifact => artifact.id === action.payload.id);
        if (index !== -1) {
          state.artifacts[index] = action.payload;
        }
        if (state.selectedArtifact?.id === action.payload.id) {
          state.selectedArtifact = action.payload;
        }
      })
      .addCase(updateArtifact.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Delete artifact
    builder
      .addCase(deleteArtifact.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(deleteArtifact.fulfilled, (state, action) => {
        state.isLoading = false;
        state.artifacts = state.artifacts.filter(artifact => artifact.id !== action.payload);
        state.totalItems -= 1;
        if (state.selectedArtifact?.id === action.payload) {
          state.selectedArtifact = null;
        }
      })
      .addCase(deleteArtifact.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Bulk delete artifacts
    builder
      .addCase(bulkDeleteArtifacts.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(bulkDeleteArtifacts.fulfilled, (state, action) => {
        state.isLoading = false;
        const deletedIds = action.payload;
        state.artifacts = state.artifacts.filter(artifact => !deletedIds.includes(artifact.id));
        state.totalItems -= deletedIds.length;
        if (state.selectedArtifact && deletedIds.includes(state.selectedArtifact.id)) {
          state.selectedArtifact = null;
        }
      })
      .addCase(bulkDeleteArtifacts.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const {
  clearError,
  setFilters,
  clearFilters,
  setSelectedArtifact,
  clearSearchResults,
  setCurrentPage,
  updateArtifactOptimistic,
} = artifactsSlice.actions;

export default artifactsSlice.reducer;